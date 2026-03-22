"""
Langflow Agent Orchestrator
Architecture: Option B (Pi coding-agent style) — extensible tool harness
with read/write/edit/bash + domain-specific Langflow tools.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from typing import Callable

import anthropic

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable

    def to_api(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def api_list(self) -> list[dict]:
        return [t.to_api() for t in self._tools.values()]

    def call(self, name: str, inputs: dict) -> str:
        tool = self.get(name)
        if not tool:
            return f"ERROR: unknown tool '{name}'"
        try:
            result = tool.fn(**inputs)
            return str(result)
        except Exception as e:
            return f"ERROR calling {name}: {e}"


# ---------------------------------------------------------------------------
# Scratch-pad (in-memory workspace)
# ---------------------------------------------------------------------------

class Workspace:
    """Simple in-memory key/value store used by tools."""

    def __init__(self):
        self._files: dict[str, str] = {}

    def write(self, path: str, content: str):
        self._files[path] = content

    def read(self, path: str) -> str:
        return self._files.get(path, f"<file '{path}' not found>")

    def edit(self, path: str, old: str, new: str) -> str:
        if path not in self._files:
            return f"ERROR: file '{path}' not found"
        if old not in self._files[path]:
            return f"ERROR: pattern not found in '{path}'"
        self._files[path] = self._files[path].replace(old, new, 1)
        return "ok"

    def list_files(self) -> list[str]:
        return list(self._files.keys())

    def dump_all(self) -> dict[str, str]:
        return dict(self._files)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def make_tools(workspace: Workspace, artifact_store: dict) -> ToolRegistry:
    registry = ToolRegistry()

    # --- generic file tools (pi-style) ---

    registry.register(Tool(
        name="write_file",
        description="Write content to a workspace file. Use for Python components, JSON flows, markdown docs.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path, e.g. 'flow.json' or 'my_component.py'"},
                "content": {"type": "string", "description": "Full file content"},
            },
            "required": ["path", "content"],
        },
        fn=lambda path, content: _write(workspace, artifact_store, path, content),
    ))

    registry.register(Tool(
        name="read_file",
        description="Read a workspace file.",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        fn=lambda path: workspace.read(path),
    ))

    registry.register(Tool(
        name="edit_file",
        description="Replace an exact substring in a workspace file.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string", "description": "Exact text to replace"},
                "new_text": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_text", "new_text"],
        },
        fn=lambda path, old_text, new_text: workspace.edit(path, old_text, new_text),
    ))

    registry.register(Tool(
        name="list_files",
        description="List all files currently in the workspace.",
        input_schema={"type": "object", "properties": {}},
        fn=lambda: json.dumps(workspace.list_files()),
    ))

    # --- Langflow-specific domain tools ---

    registry.register(Tool(
        name="generate_node_id",
        description="Generate a unique node ID suitable for a Langflow flow JSON.",
        input_schema={
            "type": "object",
            "properties": {"prefix": {"type": "string", "description": "Node type prefix, e.g. 'ChatInput'"}},
            "required": ["prefix"],
        },
        fn=lambda prefix: f"{prefix}-{uuid.uuid4().hex[:8]}",
    ))

    registry.register(Tool(
        name="validate_flow_json",
        description="Validate that a JSON string is a well-formed Langflow flow (has nodes + edges arrays).",
        input_schema={
            "type": "object",
            "properties": {"json_str": {"type": "string"}},
            "required": ["json_str"],
        },
        fn=_validate_flow,
    ))

    registry.register(Tool(
        name="validate_component_python",
        description="Check that a Python string defines a class inheriting from Component with required methods.",
        input_schema={
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
        fn=_validate_component,
    ))

    registry.register(Tool(
        name="get_langflow_schema_template",
        description="Return a minimal Langflow flow JSON template or component class template to start from.",
        input_schema={
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "enum": ["flow", "text_component", "multimodal_component"],
                    "description": "Which template to return",
                }
            },
            "required": ["template_type"],
        },
        fn=_get_template,
    ))

    return registry


def _write(workspace: Workspace, artifact_store: dict, path: str, content: str) -> str:
    workspace.write(path, content)
    artifact_store[path] = content
    return f"written {len(content)} chars to '{path}'"


def _validate_flow(json_str: str) -> str:
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return f"INVALID JSON: {e}"
    if "nodes" not in data or "edges" not in data:
        return "INVALID FLOW: missing 'nodes' or 'edges' keys"
    if not isinstance(data["nodes"], list) or not isinstance(data["edges"], list):
        return "INVALID FLOW: 'nodes' and 'edges' must be arrays"
    for i, node in enumerate(data["nodes"]):
        for key in ("id", "type", "data"):
            if key not in node:
                return f"INVALID NODE[{i}]: missing '{key}'"
    return f"VALID: {len(data['nodes'])} nodes, {len(data['edges'])} edges"


def _validate_component(code: str) -> str:
    issues = []
    if "class " not in code:
        issues.append("no class definition found")
    if "Component" not in code:
        issues.append("class must inherit from Component")
    if "inputs" not in code and "outputs" not in code:
        issues.append("missing inputs/outputs class attributes")
    if not issues:
        # Check for at least one method
        method_count = len(re.findall(r"def \w+\(self", code))
        if method_count == 0:
            issues.append("no instance methods found")
    if issues:
        return "ISSUES: " + "; ".join(issues)
    return "VALID component structure"


def _get_template(template_type: str) -> str:
    if template_type == "flow":
        return json.dumps({
            "id": f"flow-{uuid.uuid4().hex[:8]}",
            "name": "Generated Flow",
            "description": "",
            "nodes": [],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }, indent=2)

    if template_type == "text_component":
        return '''from langflow.custom import Component
from langflow.inputs import MessageTextInput, StrInput
from langflow.outputs import MessageOutput
from langflow.schema.message import Message


class MyTextComponent(Component):
    display_name = "My Text Component"
    description = "A custom text processing component."
    icon = "type"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input Text",
            info="The text to process.",
        ),
        StrInput(
            name="system_prompt",
            display_name="System Prompt",
            value="You are a helpful assistant.",
        ),
    ]

    outputs = [
        MessageOutput(name="output", display_name="Output", method="process_text"),
    ]

    def process_text(self) -> Message:
        text = self.input_text
        # TODO: implement processing logic
        return Message(text=f"Processed: {text}")
'''

    if template_type == "multimodal_component":
        return '''from langflow.custom import Component
from langflow.inputs import FileInput, MessageTextInput
from langflow.outputs import MessageOutput
from langflow.schema.message import Message
import base64


class MultiModalComponent(Component):
    display_name = "Vision Component"
    description = "Processes images with a vision-capable LLM."
    icon = "image"

    inputs = [
        FileInput(
            name="image_file",
            display_name="Image File",
            info="Upload an image (PNG, JPG, WEBP).",
            file_types=["png", "jpg", "jpeg", "webp"],
        ),
        MessageTextInput(
            name="question",
            display_name="Question",
            info="What to ask about the image.",
            value="Describe this image.",
        ),
    ]

    outputs = [
        MessageOutput(name="result", display_name="Result", method="analyze_image"),
    ]

    def analyze_image(self) -> Message:
        image_path = self.image_file
        question = self.question

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.rsplit(".", 1)[-1].lower()
        media_type = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"

        # Uses Anthropic client (injected via Langflow secret store)
        from anthropic import Anthropic
        client = Anthropic()

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": question},
                ],
            }],
        )
        return Message(text=response.content[0].text)
'''
    return "unknown template type"


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert Langflow architect and Python developer.
Your job is to generate valid Langflow artifacts from a natural language description.

You MUST produce:
1. A complete Langflow flow JSON (file: flow.json) with proper nodes and edges
2. At least one custom Python component (file: <ComponentName>.py) that inherits from Component
3. A README.md explaining how to import and use the generated artifacts

Architecture rules:
- Always call get_langflow_schema_template first to get the correct starting structure
- Always call generate_node_id for every node you create
- Always call validate_flow_json before writing the final flow.json
- Always call validate_component_python before writing the final component .py
- Nodes must have: id, type="genericNode", position (x,y), data with {id, type, node:{template, base_classes, display_name}}
- Edges must have: id, source, target, sourceHandle, targetHandle
- Langflow component inputs use classes from langflow.inputs; outputs from langflow.outputs
- For multimodal requests: generate a vision component using FileInput and base64 image encoding

Be thorough and generate production-quality code, not stubs.
Think step by step before writing each file.
"""


class LangflowAgent:
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.workspace = Workspace()
        self.artifacts: dict[str, str] = {}
        self.registry = make_tools(self.workspace, self.artifacts)
        self.conversation: list[dict] = []
        self.tool_calls_log: list[dict] = []

    def run(self, user_description: str, max_iterations: int = 20) -> dict:
        """Run the agent loop; return generated artifacts."""
        self.conversation = [{"role": "user", "content": user_description}]

        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=self.registry.api_list(),
                messages=self.conversation,
            )

            # Serialize the assistant turn to plain dicts (SDK returns objects)
            # This also ensures the conversation history stays JSON-safe.
            assistant_content = self._serialize_content(response.content)
            self.conversation.append({"role": "assistant", "content": assistant_content})

            # Check stop condition first
            if response.stop_reason == "end_turn":
                break

            # Process tool calls — CRITICAL: every tool_use block in the
            # assistant turn must have a matching tool_result in the very next
            # user turn. Collect ALL of them before appending.
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in assistant_content:
                    if block.get("type") == "tool_use":
                        result = self.registry.call(block["name"], block["input"])
                        self.tool_calls_log.append({
                            "tool": block["name"],
                            "input": block["input"],
                            "result": result,
                        })
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": result,
                        })

                # Only append if we actually have results (guards against
                # edge case where stop_reason=tool_use but no tool_use blocks)
                if tool_results:
                    self.conversation.append({"role": "user", "content": tool_results})

        return self.artifacts

    @staticmethod
    def _serialize_content(content: list) -> list[dict]:
        """Convert SDK response content blocks to plain dicts for safe re-use
        in subsequent API calls. Handles text, tool_use, and unknown block types."""
        serialized = []
        for block in content:
            if hasattr(block, "type"):
                btype = block.type
                if btype == "text":
                    serialized.append({"type": "text", "text": block.text})
                elif btype == "tool_use":
                    serialized.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                else:
                    # Forward-compatible: pass unknown block types through as dicts
                    serialized.append(vars(block) if hasattr(block, "__dict__") else {"type": btype})
            elif isinstance(block, dict):
                serialized.append(block)
        return serialized