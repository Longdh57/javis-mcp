#!/usr/bin/env python3
"""
Fetches TRELLO_URL/openapi.json and regenerates trello_tools.py with
typed MCP tool functions for each endpoint.

Usage:
    python generate_trello_tools.py
"""
import os
import re
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

TRELLO_URL = os.environ.get("TRELLO_URL", "").rstrip("/")

OPENAPI_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}


def resolve_ref(spec: dict, ref: str) -> dict:
    parts = ref.lstrip("#/").split("/")
    node = spec
    for part in parts:
        node = node[part]
    return node


def get_python_type(spec: dict, schema: dict) -> str:
    if not schema:
        return "Any"
    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])
    typ = schema.get("type", "object")
    if typ == "array":
        items = schema.get("items", {})
        inner = get_python_type(spec, items) if items else "Any"
        return f"list[{inner}]"
    return OPENAPI_TYPE_MAP.get(typ, "dict")


def to_snake_case(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def sanitize_identifier(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name and name[0].isdigit():
        name = "_" + name
    return name or "_"


def safe_description(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()


def generate_trello_tools(spec: dict) -> str:
    lines = [
        "# AUTO-GENERATED — do not edit manually.",
        "# Re-generate with: python generate_trello_tools.py",
        "",
        "import os",
        "import httpx",
        "from typing import Any, Optional",
        "",
        'TRELLO_URL = os.environ.get("TRELLO_URL", "").rstrip("/")',
        "",
        "",
    ]

    functions: list[tuple[str, str]] = []  # (func_name, description)

    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue

            operation_id = operation.get("operationId") or f"{method}_{path}"
            func_name = sanitize_identifier(to_snake_case(operation_id))
            description = safe_description(
                operation.get("summary") or operation.get("description") or func_name
            )

            # --- Collect parameters ---
            # Each entry: (py_name, py_type, location, required, original_name)
            all_params: list[tuple[str, str, str, bool, str]] = []

            for param in operation.get("parameters", []):
                if "$ref" in param:
                    param = resolve_ref(spec, param["$ref"])
                orig_name = param["name"]
                py_name = sanitize_identifier(orig_name)
                location = param.get("in", "query")
                required = param.get("required", location == "path")
                py_type = get_python_type(spec, param.get("schema", {}))
                all_params.append((py_name, py_type, location, required, orig_name))

            # --- Request body ---
            req_body = operation.get("requestBody", {})
            if "$ref" in req_body:
                req_body = resolve_ref(spec, req_body["$ref"])
            if req_body:
                content = req_body.get("content", {})
                body_schema = content.get("application/json", {}).get("schema", {})
                if "$ref" in body_schema:
                    body_schema = resolve_ref(spec, body_schema["$ref"])
                if body_schema.get("type") == "object":
                    props = body_schema.get("properties", {})
                    required_fields = set(body_schema.get("required", []))
                    for prop_name, prop_schema in props.items():
                        py_name = sanitize_identifier(prop_name)
                        py_type = get_python_type(spec, prop_schema)
                        is_req = prop_name in required_fields or req_body.get("required", False)
                        all_params.append((py_name, py_type, "body", is_req, prop_name))
                elif body_schema:
                    py_type = get_python_type(spec, body_schema)
                    is_req = req_body.get("required", False)
                    all_params.append(("body", py_type, "body", is_req, None))

            # --- Build function signature ---
            required_params = [p for p in all_params if p[3]]
            optional_params = [p for p in all_params if not p[3]]

            sig_parts = []
            for py_name, py_type, *_ in required_params:
                sig_parts.append(f"{py_name}: {py_type}")
            for py_name, py_type, *_ in optional_params:
                sig_parts.append(f"{py_name}: Optional[{py_type}] = None")

            sig = ", ".join(sig_parts)

            # --- Build function body ---
            body_lines: list[str] = []

            # URL with path params substituted
            url_path = path
            for py_name, _, loc, _, orig_name in all_params:
                if loc == "path":
                    url_path = url_path.replace(f"{{{orig_name}}}", f"{{{py_name}}}")
            body_lines.append(f'    url = f"{{TRELLO_URL}}{url_path}"')

            # Query params dict (skip None values)
            query_entries = [(py_name, orig) for py_name, _, loc, _, orig in all_params if loc == "query"]
            if query_entries:
                body_lines.append("    query_params = {k: v for k, v in {")
                for py_name, orig_name in query_entries:
                    body_lines.append(f'        "{orig_name}": {py_name},')
                body_lines.append("    }.items() if v is not None}")
            else:
                body_lines.append("    query_params = {}")

            # JSON body
            body_entries = [(py_name, orig) for py_name, _, loc, _, orig in all_params if loc == "body"]
            if body_entries:
                if len(body_entries) == 1 and body_entries[0][0] == "body":
                    body_lines.append("    json_data = body")
                else:
                    body_lines.append("    json_data = {k: v for k, v in {")
                    for py_name, orig_name in body_entries:
                        body_lines.append(f'        "{orig_name}": {py_name},')
                    body_lines.append("    }.items() if v is not None}")
            else:
                body_lines.append("    json_data = None")

            body_lines.append("    with httpx.Client() as client:")
            body_lines.append(f"        response = client.{method.lower()}(url, params=query_params, json=json_data)")
            body_lines.append("        response.raise_for_status()")
            body_lines.append("        return response.json()")

            # Write function
            lines.append(f"def {func_name}({sig}) -> Any:")
            lines.append(f'    """{description}"""')
            lines.extend(body_lines)
            lines.append("")
            lines.append("")

            functions.append((func_name, description))

    # register_trello_tools
    lines.append("def register_trello_tools(mcp) -> None:")
    lines.append('    """Register all generated Trello API tools with the MCP server."""')
    if functions:
        for func_name, description in functions:
            lines.append(f'    mcp.tool(description="{safe_description(description)}")({func_name})')
    else:
        lines.append("    pass  # No endpoints found in spec")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    if not TRELLO_URL:
        print("ERROR: TRELLO_URL is not set in .env")
        raise SystemExit(1)

    spec_url = f"{TRELLO_URL}/openapi.json"
    print(f"Fetching {spec_url} ...")
    try:
        response = httpx.get(spec_url, timeout=15)
        response.raise_for_status()
        spec = response.json()
    except httpx.HTTPError as e:
        print(f"ERROR: Failed to fetch spec: {e}")
        raise SystemExit(1)

    paths = spec.get("paths", {})
    endpoint_count = sum(
        1
        for item in paths.values()
        for m in item
        if m.lower() in ("get", "post", "put", "patch", "delete")
    )
    print(f"Found {len(paths)} path(s), {endpoint_count} endpoint(s)")

    code = generate_trello_tools(spec)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trello_tools.py")
    with open(output_path, "w") as f:
        f.write(code)

    print(f"Generated {output_path} with {endpoint_count} tool(s)")
    print("Done. Add `from trello_tools import register_trello_tools` to main.py if not already done.")


if __name__ == "__main__":
    main()
