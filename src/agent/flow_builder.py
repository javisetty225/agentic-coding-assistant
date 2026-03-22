"""
Langflow Flow Builder
Domain helpers that construct valid Langflow flow JSON programmatically.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


def node_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def edge_id(source: str, target: str) -> str:
    return f"reactflow__edge-{source}-{target}"


# ---------------------------------------------------------------------------
# Node builders
# ---------------------------------------------------------------------------

@dataclass
class NodePosition:
    x: float = 0.0
    y: float = 0.0


def _base_node(
    nid: str,
    display_name: str,
    base_classes: list[str],
    template: dict,
    position: NodePosition | None = None,
    description: str = "",
) -> dict:
    pos = position or NodePosition()
    return {
        "id": nid,
        "type": "genericNode",
        "position": {"x": pos.x, "y": pos.y},
        "data": {
            "id": nid,
            "type": display_name,
            "node": {
                "template": template,
                "description": description,
                "base_classes": base_classes,
                "display_name": display_name,
                "documentation": "",
                "custom_fields": {},
                "output_types": base_classes,
                "pinned": False,
            },
        },
        "selected": False,
        "positionAbsolute": {"x": pos.x, "y": pos.y},
        "dragging": False,
        "width": 384,
        "height": 288,
    }


def chat_input_node(nid: str | None = None, position: NodePosition | None = None) -> dict:
    nid = nid or node_id("ChatInput")
    return _base_node(
        nid=nid,
        display_name="ChatInput",
        base_classes=["Message"],
        description="Get chat inputs from the Playground.",
        position=position or NodePosition(x=50, y=200),
        template={
            "input_value": {
                "type": "str",
                "required": False,
                "display_name": "Text",
                "multiline": True,
                "value": "",
                "show": True,
                "name": "input_value",
                "advanced": False,
                "dynamic": False,
                "info": "",
            },
            "should_store_message": {
                "type": "bool",
                "value": True,
                "show": True,
                "name": "should_store_message",
                "display_name": "Store Messages",
                "advanced": True,
                "dynamic": False,
                "info": "",
            },
            "_type": "CustomComponent",
            "code": {"type": "code", "show": False, "value": "", "name": "code", "dynamic": True},
        },
    )


def chat_output_node(nid: str | None = None, position: NodePosition | None = None) -> dict:
    nid = nid or node_id("ChatOutput")
    return _base_node(
        nid=nid,
        display_name="ChatOutput",
        base_classes=["Message"],
        description="Display a chat message in the Playground.",
        position=position or NodePosition(x=900, y=200),
        template={
            "input_value": {
                "type": "str",
                "required": False,
                "display_name": "Text",
                "multiline": True,
                "value": "",
                "show": True,
                "name": "input_value",
                "advanced": False,
                "dynamic": False,
                "info": "",
            },
            "should_store_message": {
                "type": "bool",
                "value": True,
                "show": True,
                "name": "should_store_message",
                "display_name": "Store Messages",
                "advanced": True,
                "dynamic": False,
                "info": "",
            },
            "_type": "CustomComponent",
            "code": {"type": "code", "show": False, "value": "", "name": "code", "dynamic": True},
        },
    )


def openai_model_node(nid: str | None = None, position: NodePosition | None = None, model: str = "gpt-4o") -> dict:
    nid = nid or node_id("OpenAIModel")
    return _base_node(
        nid=nid,
        display_name="OpenAIModel",
        base_classes=["Message", "LanguageModel"],
        description="Generate text using OpenAI LLMs.",
        position=position or NodePosition(x=500, y=200),
        template={
            "input_value": {
                "type": "str",
                "required": False,
                "display_name": "Input",
                "value": "",
                "show": True,
                "name": "input_value",
                "advanced": False,
                "dynamic": False,
                "info": "",
            },
            "model_name": {
                "type": "str",
                "required": True,
                "display_name": "Model Name",
                "value": model,
                "show": True,
                "name": "model_name",
                "options": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "advanced": False,
                "dynamic": False,
                "info": "",
            },
            "api_key": {
                "type": "str",
                "required": True,
                "display_name": "OpenAI API Key",
                "value": "",
                "show": True,
                "name": "api_key",
                "password": True,
                "advanced": False,
                "dynamic": False,
                "info": "",
            },
            "system_message": {
                "type": "str",
                "required": False,
                "display_name": "System Message",
                "value": "You are a helpful assistant.",
                "show": True,
                "name": "system_message",
                "multiline": True,
                "advanced": False,
                "dynamic": False,
                "info": "",
            },
            "temperature": {
                "type": "float",
                "required": False,
                "display_name": "Temperature",
                "value": 0.7,
                "show": True,
                "name": "temperature",
                "advanced": True,
                "dynamic": False,
                "info": "",
            },
            "_type": "CustomComponent",
            "code": {"type": "code", "show": False, "value": "", "name": "code", "dynamic": True},
        },
    )


def custom_component_node(
    nid: str | None = None,
    display_name: str = "CustomComponent",
    component_code: str = "",
    base_classes: list[str] | None = None,
    position: NodePosition | None = None,
    input_fields: list[dict] | None = None,
) -> dict:
    nid = nid or node_id(display_name.replace(" ", ""))
    template: dict = {
        "_type": "CustomComponent",
        "code": {
            "type": "code",
            "show": True,
            "value": component_code,
            "name": "code",
            "dynamic": True,
        },
    }
    for f in (input_fields or []):
        template[f["name"]] = f

    return _base_node(
        nid=nid,
        display_name=display_name,
        base_classes=base_classes or ["Message"],
        description=f"Custom component: {display_name}",
        position=position or NodePosition(x=500, y=200),
        template=template,
    )


# ---------------------------------------------------------------------------
# Edge builder
# ---------------------------------------------------------------------------

def make_edge(
    source_id: str,
    target_id: str,
    source_handle_suffix: str = "Message",
    target_handle_field: str = "input_value",
) -> dict:
    eid = edge_id(source_id, target_id)
    return {
        "id": eid,
        "source": source_id,
        "target": target_id,
        "sourceHandle": f"{source_id}|{source_handle_suffix}|0",
        "targetHandle": f"{target_id}|{target_handle_field}|Message",
        "data": {
            "targetHandle": {
                "fieldName": target_handle_field,
                "id": target_id,
                "inputTypes": ["Message"],
                "type": "Message",
            },
            "sourceHandle": {
                "baseClasses": [source_handle_suffix],
                "dataType": source_handle_suffix,
                "id": source_id,
                "name": source_handle_suffix,
                "output_types": [source_handle_suffix],
            },
        },
        "type": "default",
        "animated": False,
        "selected": False,
    }


# ---------------------------------------------------------------------------
# Flow assembler
# ---------------------------------------------------------------------------

def build_flow(
    name: str,
    nodes: list[dict],
    edges: list[dict],
    description: str = "",
) -> dict:
    return {
        "id": f"flow-{uuid.uuid4().hex[:8]}",
        "name": name,
        "description": description,
        "nodes": nodes,
        "edges": edges,
        "viewport": {"x": 0, "y": 0, "zoom": 0.75},
    }