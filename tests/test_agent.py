"""
Tests for the Langflow Agent
Run: python -m pytest tests/ -v
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.harness.flow_builder import (
    build_flow,
    chat_input_node,
    chat_output_node,
    make_edge,
    node_id,
    openai_model_node,
)
from src.agent.orchestrator import (
    Workspace,
    _validate_component,
    _validate_flow,
    _get_template,
)


# ---------------------------------------------------------------------------
# Flow builder tests
# ---------------------------------------------------------------------------

class TestNodeIds:
    def test_format(self):
        nid = node_id("ChatInput")
        assert nid.startswith("ChatInput-")
        assert len(nid) == len("ChatInput-") + 8

    def test_unique(self):
        ids = {node_id("X") for _ in range(100)}
        assert len(ids) == 100


class TestChatInputNode:
    def test_structure(self):
        n = chat_input_node()
        assert n["type"] == "genericNode"
        assert "id" in n
        assert n["data"]["node"]["display_name"] == "ChatInput"
        assert "Message" in n["data"]["node"]["base_classes"]

    def test_custom_id(self):
        n = chat_input_node(nid="my-id")
        assert n["id"] == "my-id"

    def test_has_template(self):
        n = chat_input_node()
        assert "input_value" in n["data"]["node"]["template"]


class TestEdge:
    def test_structure(self):
        e = make_edge("A", "B")
        assert e["source"] == "A"
        assert e["target"] == "B"
        assert "id" in e
        assert e["sourceHandle"].startswith("A|")
        assert e["targetHandle"].startswith("B|")


class TestBuildFlow:
    def test_complete_flow(self):
        inp = chat_input_node()
        llm = openai_model_node()
        out = chat_output_node()
        e1 = make_edge(inp["id"], llm["id"])
        e2 = make_edge(llm["id"], out["id"])

        flow = build_flow("Test Flow", [inp, llm, out], [e1, e2])

        assert flow["name"] == "Test Flow"
        assert len(flow["nodes"]) == 3
        assert len(flow["edges"]) == 2
        assert "viewport" in flow

    def test_flow_is_json_serializable(self):
        flow = build_flow("JSON Test", [chat_input_node()], [])
        serialized = json.dumps(flow)
        restored = json.loads(serialized)
        assert restored["name"] == "JSON Test"


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidateFlow:
    def test_valid_flow(self):
        flow = build_flow("V", [chat_input_node()], [])
        result = _validate_flow(json.dumps(flow))
        assert result.startswith("VALID")

    def test_invalid_json(self):
        result = _validate_flow("{not valid json")
        assert "INVALID JSON" in result

    def test_missing_nodes(self):
        result = _validate_flow(json.dumps({"edges": []}))
        assert "INVALID FLOW" in result

    def test_missing_edges(self):
        result = _validate_flow(json.dumps({"nodes": []}))
        assert "INVALID FLOW" in result

    def test_malformed_node(self):
        result = _validate_flow(json.dumps({"nodes": [{"bad": True}], "edges": []}))
        assert "INVALID NODE" in result


class TestValidateComponent:
    VALID_COMPONENT = '''
from langflow.custom import Component
from langflow.inputs import MessageTextInput
from langflow.outputs import MessageOutput
from langflow.schema.message import Message

class MyComp(Component):
    inputs = [MessageTextInput(name="x", display_name="X")]
    outputs = [MessageOutput(name="out", display_name="Out", method="run")]

    def run(self) -> Message:
        return Message(text="hello")
'''

    def test_valid(self):
        result = _validate_component(self.VALID_COMPONENT)
        assert result == "VALID component structure"

    def test_missing_class(self):
        result = _validate_component("def foo(): pass")
        assert "ISSUES" in result
        assert "no class definition" in result

    def test_missing_component_base(self):
        result = _validate_component("class MyClass:\n    pass")
        assert "ISSUES" in result
        assert "Component" in result

    def test_no_methods(self):
        result = _validate_component("class MyComp(Component):\n    inputs = []\n    outputs = []")
        assert "ISSUES" in result
        assert "no instance methods" in result


class TestTemplates:
    def test_flow_template_valid(self):
        template = _get_template("flow")
        data = json.loads(template)
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)

    def test_text_component_template(self):
        template = _get_template("text_component")
        assert "class " in template
        assert "Component" in template
        assert "inputs" in template
        assert "outputs" in template

    def test_multimodal_template(self):
        template = _get_template("multimodal_component")
        assert "FileInput" in template
        assert "base64" in template
        assert "image" in template.lower()

    def test_unknown_template(self):
        result = _get_template("unknown_type")
        assert "unknown" in result.lower()


# ---------------------------------------------------------------------------
# Workspace tests
# ---------------------------------------------------------------------------

class TestWorkspace:
    def test_write_read(self):
        ws = Workspace()
        ws.write("test.py", "print('hello')")
        assert ws.read("test.py") == "print('hello')"

    def test_missing_file(self):
        ws = Workspace()
        result = ws.read("nonexistent.txt")
        assert "not found" in result

    def test_edit(self):
        ws = Workspace()
        ws.write("f.py", "x = 1\ny = 2\n")
        result = ws.edit("f.py", "x = 1", "x = 99")
        assert result == "ok"
        assert "x = 99" in ws.read("f.py")
        assert "y = 2" in ws.read("f.py")

    def test_edit_not_found(self):
        ws = Workspace()
        ws.write("f.py", "hello")
        result = ws.edit("f.py", "MISSING", "new")
        assert "ERROR" in result

    def test_list_files(self):
        ws = Workspace()
        ws.write("a.py", "")
        ws.write("b.json", "")
        files = ws.list_files()
        assert "a.py" in files
        assert "b.json" in files

    def test_overwrite(self):
        ws = Workspace()
        ws.write("x.txt", "original")
        ws.write("x.txt", "updated")
        assert ws.read("x.txt") == "updated"


# ---------------------------------------------------------------------------
# Generated artifact smoke tests
# ---------------------------------------------------------------------------

class TestGeneratedArtifacts:
    """Validate the pre-generated artifacts in the generated/ directory."""

    def _load_json(self, path: str) -> dict:
        with open(path) as f:
            return json.load(f)

    def test_flow_json_valid(self):
        import os
        flow_path = os.path.join(os.path.dirname(__file__), "..", "generated", "flow.json")
        if not os.path.exists(flow_path):
            return  # skip if not generated yet
        flow = self._load_json(flow_path)
        assert "nodes" in flow
        assert "edges" in flow
        assert len(flow["nodes"]) >= 2
        for node in flow["nodes"]:
            assert "id" in node
            assert "type" in node
            assert "data" in node

    def test_smart_summarizer_valid(self):
        import os
        py_path = os.path.join(os.path.dirname(__file__), "..", "generated", "SmartSummarizer.py")
        if not os.path.exists(py_path):
            return
        with open(py_path) as f:
            code = f.read()
        result = _validate_component(code)
        assert result == "VALID component structure"

    def test_vision_analyzer_valid(self):
        import os
        py_path = os.path.join(os.path.dirname(__file__), "..", "generated", "VisionAnalyzer.py")
        if not os.path.exists(py_path):
            return
        with open(py_path) as f:
            code = f.read()
        result = _validate_component(code)
        assert result == "VALID component structure"

    def test_movie_recommender_valid(self):
        import os
        py_path = os.path.join(os.path.dirname(__file__), "..", "generated", "MovieRecommenderComponent.py")
        if not os.path.exists(py_path):
            return
        with open(py_path) as f:
            code = f.read()
        result = _validate_component(code)
        assert result == "VALID component structure"

    def test_all_generated_components_valid(self):
        """Validate every .py file in generated/ is a valid Langflow component."""
        import os
        generated_dir = os.path.join(os.path.dirname(__file__), "..", "generated")
        if not os.path.exists(generated_dir):
            return
        py_files = [f for f in os.listdir(generated_dir) if f.endswith(".py")]
        assert len(py_files) > 0, "No Python components found in generated/"
        for fname in py_files:
            path = os.path.join(generated_dir, fname)
            with open(path) as f:
                code = f.read()
            result = _validate_component(code)
            assert result == "VALID component structure", f"{fname} failed: {result}"

    def test_flow_has_minimum_nodes(self):
        """Flow must have at least 3 nodes: input, component, output."""
        import os
        flow_path = os.path.join(os.path.dirname(__file__), "..", "generated", "flow.json")
        if not os.path.exists(flow_path):
            return
        flow = self._load_json(flow_path)
        assert len(flow["nodes"]) >= 3, "Flow needs at least 3 nodes"

    def test_flow_has_edges(self):
        """Flow must have edges connecting nodes."""
        import os
        flow_path = os.path.join(os.path.dirname(__file__), "..", "generated", "flow.json")
        if not os.path.exists(flow_path):
            return
        flow = self._load_json(flow_path)
        assert len(flow["edges"]) >= 1, "Flow must have at least 1 edge"

    def test_flow_edges_reference_valid_nodes(self):
        """Every edge source and target must reference an existing node id."""
        import os
        flow_path = os.path.join(os.path.dirname(__file__), "..", "generated", "flow.json")
        if not os.path.exists(flow_path):
            return
        flow = self._load_json(flow_path)
        node_ids = {n["id"] for n in flow["nodes"]}
        for edge in flow["edges"]:
            assert edge["source"] in node_ids, f"Edge source '{edge['source']}' not in nodes"
            assert edge["target"] in node_ids, f"Edge target '{edge['target']}' not in nodes"

    def test_readme_exists_and_not_empty(self):
        """README.md should be generated alongside the flow."""
        import os
        readme_path = os.path.join(os.path.dirname(__file__), "..", "generated", "README.md")
        if not os.path.exists(readme_path):
            return
        with open(readme_path) as f:
            content = f.read()
        assert len(content) > 100, "README.md is too short or empty"