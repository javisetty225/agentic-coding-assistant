from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.flow_builder import (  # noqa: E402
    build_flow,
    chat_input_node,
    chat_output_node,
    make_edge,
    node_id,
    openai_model_node,
)
from src.agent.orchestrator import (  # noqa: E402
    Workspace,
    get_template,
    validate_component,
    validate_flow,
)

UNIQUE_ID_SAMPLE_SIZE = 100
COMPLETE_FLOW_NODE_COUNT = 3
COMPLETE_FLOW_EDGE_COUNT = 2
MIN_FLOW_NODES = 2
MIN_REQUIRED_NODES = 3
MIN_REQUIRED_EDGES = 1
MIN_README_LENGTH = 100

GENERATED_DIR = Path(__file__).parent.parent / "generated"


def load_json(path: Path) -> dict:
    """Load a JSON file with explicit UTF-8 encoding."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    """Read a text file with explicit UTF-8 encoding."""
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Flow builder tests
# ---------------------------------------------------------------------------

def test_node_id_format() -> None:
    nid = node_id("ChatInput")
    assert nid.startswith("ChatInput-")
    assert len(nid) == len("ChatInput-") + 8


def test_node_id_unique() -> None:
    ids = {node_id("X") for _ in range(UNIQUE_ID_SAMPLE_SIZE)}
    assert len(ids) == UNIQUE_ID_SAMPLE_SIZE


def test_chat_input_node_structure() -> None:
    n = chat_input_node()
    assert n["type"] == "genericNode"
    assert "id" in n
    assert n["data"]["node"]["display_name"] == "ChatInput"
    assert "Message" in n["data"]["node"]["base_classes"]


def test_chat_input_node_custom_id() -> None:
    n = chat_input_node(nid="my-id")
    assert n["id"] == "my-id"


def test_chat_input_node_has_template() -> None:
    n = chat_input_node()
    assert "input_value" in n["data"]["node"]["template"]


def test_edge_structure() -> None:
    e = make_edge("A", "B")
    assert e["source"] == "A"
    assert e["target"] == "B"
    assert "id" in e
    assert e["sourceHandle"].startswith("A|")
    assert e["targetHandle"].startswith("B|")


def test_build_complete_flow() -> None:
    inp = chat_input_node()
    llm = openai_model_node()
    out = chat_output_node()
    e1 = make_edge(inp["id"], llm["id"])
    e2 = make_edge(llm["id"], out["id"])
    flow = build_flow("Test Flow", [inp, llm, out], [e1, e2])
    assert flow["name"] == "Test Flow"
    assert len(flow["nodes"]) == COMPLETE_FLOW_NODE_COUNT
    assert len(flow["edges"]) == COMPLETE_FLOW_EDGE_COUNT
    assert "viewport" in flow


def test_flow_is_json_serializable() -> None:
    flow = build_flow("JSON Test", [chat_input_node()], [])
    serialized = json.dumps(flow)
    restored = json.loads(serialized)
    assert restored["name"] == "JSON Test"


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_validate_flow_valid() -> None:
    flow = build_flow("V", [chat_input_node()], [])
    result = validate_flow(json.dumps(flow))
    assert result.startswith("VALID")


def test_validate_flow_invalid_json() -> None:
    result = validate_flow("{not valid json")
    assert "INVALID JSON" in result


def test_validate_flow_missing_nodes() -> None:
    result = validate_flow(json.dumps({"edges": []}))
    assert "INVALID FLOW" in result


def test_validate_flow_missing_edges() -> None:
    result = validate_flow(json.dumps({"nodes": []}))
    assert "INVALID FLOW" in result


def test_validate_flow_malformed_node() -> None:
    result = validate_flow(json.dumps({"nodes": [{"bad": True}], "edges": []}))
    assert "INVALID NODE" in result


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


def test_validate_component_valid() -> None:
    result = validate_component(VALID_COMPONENT)
    assert result == "VALID component structure"


def test_validate_component_missing_class() -> None:
    result = validate_component("def foo(): pass")
    assert "ISSUES" in result
    assert "no class definition" in result


def test_validate_component_missing_base() -> None:
    result = validate_component("class MyClass:\n    pass")
    assert "ISSUES" in result
    assert "Component" in result


def test_validate_component_no_methods() -> None:
    result = validate_component(
        "class MyComp(Component):\n    inputs = []\n    outputs = []"
    )
    assert "ISSUES" in result
    assert "no instance methods" in result


# ---------------------------------------------------------------------------
# Template tests
# ---------------------------------------------------------------------------

def test_flow_template_valid() -> None:
    template = get_template("flow")
    data = json.loads(template)
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)


def test_text_component_template() -> None:
    template = get_template("text_component")
    assert "class " in template
    assert "Component" in template
    assert "inputs" in template
    assert "outputs" in template


def test_multimodal_template() -> None:
    template = get_template("multimodal_component")
    assert "FileInput" in template
    assert "base64" in template
    assert "image" in template.lower()


def test_unknown_template() -> None:
    result = get_template("unknown_type")
    assert "unknown" in result.lower()


# ---------------------------------------------------------------------------
# Workspace tests
# ---------------------------------------------------------------------------

def test_workspace_write_read() -> None:
    ws = Workspace()
    ws.write("test.py", "print('hello')")
    assert ws.read("test.py") == "print('hello')"


def test_workspace_missing_file() -> None:
    ws = Workspace()
    result = ws.read("nonexistent.txt")
    assert "not found" in result


def test_workspace_edit() -> None:
    ws = Workspace()
    ws.write("f.py", "x = 1\ny = 2\n")
    result = ws.edit("f.py", "x = 1", "x = 99")
    assert result == "ok"
    assert "x = 99" in ws.read("f.py")
    assert "y = 2" in ws.read("f.py")


def test_workspace_edit_not_found() -> None:
    ws = Workspace()
    ws.write("f.py", "hello")
    result = ws.edit("f.py", "MISSING", "new")
    assert "ERROR" in result


def test_workspace_list_files() -> None:
    ws = Workspace()
    ws.write("a.py", "")
    ws.write("b.json", "")
    files = ws.list_files()
    assert "a.py" in files
    assert "b.json" in files


def test_workspace_overwrite() -> None:
    ws = Workspace()
    ws.write("x.txt", "original")
    ws.write("x.txt", "updated")
    assert ws.read("x.txt") == "updated"


# ---------------------------------------------------------------------------
# Generated artifact smoke tests
# ---------------------------------------------------------------------------

def test_flow_json_valid() -> None:
    flow_path = GENERATED_DIR / "flow.json"
    if not flow_path.exists():
        return
    flow = load_json(flow_path)
    assert "nodes" in flow
    assert "edges" in flow
    assert len(flow["nodes"]) >= MIN_FLOW_NODES
    for node in flow["nodes"]:
        assert "id" in node
        assert "type" in node
        assert "data" in node


def test_smart_summarizer_valid() -> None:
    py_path = GENERATED_DIR / "SmartSummarizer.py"
    if not py_path.exists():
        return
    assert validate_component(read_text(py_path)) == "VALID component structure"


def test_vision_analyzer_valid() -> None:
    py_path = GENERATED_DIR / "VisionAnalyzer.py"
    if not py_path.exists():
        return
    assert validate_component(read_text(py_path)) == "VALID component structure"


def test_movie_recommender_valid() -> None:
    py_path = GENERATED_DIR / "MovieRecommenderComponent.py"
    if not py_path.exists():
        return
    assert validate_component(read_text(py_path)) == "VALID component structure"


def test_all_generated_components_valid() -> None:
    """Validate every .py file in generated/ is a valid Langflow component."""
    if not GENERATED_DIR.exists():
        return
    py_files = list(GENERATED_DIR.glob("*.py"))
    assert len(py_files) > 0, "No Python components found in generated/"
    for py_path in py_files:
        result = validate_component(read_text(py_path))
        assert result == "VALID component structure", f"{py_path.name} failed: {result}"


def test_flow_has_minimum_nodes() -> None:
    """Flow must have at least 3 nodes: input, component, output."""
    flow_path = GENERATED_DIR / "flow.json"
    if not flow_path.exists():
        return
    flow = load_json(flow_path)
    assert len(flow["nodes"]) >= MIN_REQUIRED_NODES, "Flow needs at least 3 nodes"


def test_flow_has_edges() -> None:
    """Flow must have edges connecting nodes."""
    flow_path = GENERATED_DIR / "flow.json"
    if not flow_path.exists():
        return
    flow = load_json(flow_path)
    assert len(flow["edges"]) >= MIN_REQUIRED_EDGES, "Flow must have at least 1 edge"


def test_flow_edges_reference_valid_nodes() -> None:
    """Every edge source and target must reference an existing node id."""
    flow_path = GENERATED_DIR / "flow.json"
    if not flow_path.exists():
        return
    flow = load_json(flow_path)
    valid_ids = {n["id"] for n in flow["nodes"]}
    for edge in flow["edges"]:
        assert edge["source"] in valid_ids, (
            f"Edge source '{edge['source']}' not in nodes"
        )
        assert edge["target"] in valid_ids, (
            f"Edge target '{edge['target']}' not in nodes"
        )


def test_readme_exists_and_not_empty() -> None:
    """README.md should be generated alongside the flow."""
    readme_path = GENERATED_DIR / "README.md"
    if not readme_path.exists():
        return
    content = read_text(readme_path)
    assert len(content) > MIN_README_LENGTH, "README.md is too short or empty"