import os
import pkgutil
import importlib
import sys
import typing
import inspect
from pydantic import BaseModel
# Add the project root to sys.path so we can import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import backend.schema as schema  # noqa
from backend.schema.messaging.messages import PubSubMessage, APIMessages, APIMessageResponses  # noqa
from backend.schema.orm.base_schema import DatabaseSchema  # noqa


FRONTEND_SCHEMA_DIR = "frontend/src/schema"


def get_messages():
    """
    Recursively finds all Pydantic models in the backend.schema package,
    excluding PubSub messages which are for internal backend communication.
    """
    models = []
    for _, name, _ in pkgutil.walk_packages(schema.__path__, schema.__name__ + "."):
        try:
            module = importlib.import_module(name)
            for _, obj in inspect.getmembers(module):
                if (inspect.isclass(obj)
                        and issubclass(obj, BaseModel)
                        and obj is not BaseModel):
                    # Only include models defined in their own module
                    # (not imported ones)
                    if obj.__module__ == name:
                        # Exclude DatabaseSchema but allow PubSubMessage
                        if not issubclass(obj, DatabaseSchema):
                            models.append(obj)
        except ImportError as e:
            print(f"Failed to import {name}: {e}")
    return models


def map_json_type_to_ts(prop: dict) -> str:
    if "$ref" in prop:
        name = prop["$ref"].split("/")[-1]
        return name.replace("[", "_").replace("]", "")

    if "anyOf" in prop:
        # Filter out nulls to handle Optional[] cleanly if needed,
        # or just map all options.
        types = [map_json_type_to_ts(p) for p in prop["anyOf"]]
        return " | ".join(sorted(set(types)))

    t = prop.get("type")

    if "const" in prop:
        return f'"{prop["const"]}"'

    if t == "string":
        if "enum" in prop:
            return " | ".join([f'"{e}"' for e in prop["enum"]])
        return "string"
    if t in ["integer", "number"]:
        return "number"
    if t == "boolean":
        return "boolean"
    if t == "array":
        items = prop.get("items", {})
        return f"{map_json_type_to_ts(items)}[]"
    if t == "object":
        if "additionalProperties" in prop:
            ap = prop["additionalProperties"]
            if isinstance(ap, bool):
                return "{ [key: string]: any }" if ap else "object"
            val_type = map_json_type_to_ts(ap)
            return f"{{ [key: string]: {val_type} }}"
        return "any"
    if t == "null":
        return "null"

    return "any"

def generate_interface(name: str, schema_dict: dict, required: set) -> list:
    """Generates the TypeScript interface block."""
    lines = []
    if "description" in schema_dict:
        lines.append(f"/**\n * {schema_dict['description']}\n */")
    
    lines.append(f"export interface {name} {{")
    
    for field_name, field_schema in schema_dict.get("properties", {}).items():
        ts_type = map_json_type_to_ts(field_schema)
        
        # Discriminators and Consts are never optional
        is_const = "const" in field_schema or ("enum" in field_schema and len(field_schema["enum"]) == 1)
        is_optional = (field_name not in required) and (not is_const) and (field_name != "name")
        
        # Nullable check
        if "null" in ts_type.split(" | "):
            is_optional = True
            ts_type = ts_type.replace(" | null", "").replace("null | ", "")

        lines.append(f"  {field_name}{'?' if is_optional else ''}: {ts_type};")
    
    lines.append("}\n")
    return lines

def generate_factory(name: str, schema_dict: dict) -> list:
    """Generates a TypeScript factory using a single object argument."""
    props = schema_dict.get("properties", {})
    required = schema_dict.get("required", [])
    
    # If there are no properties (like a base 'Payload' class), 
    # the factory takes no arguments.
    if not props:
        return [
            "/**",
            f" * Factory to create an empty {name} object.",
            " */",
            f"export function create{name}(): {name} {{",
            "  return {};",
            "}\n"
        ]
    if len(required) == 1 and len(props) == 1:
        field_name = required[0]
        field_schema = props[field_name]
        ts_type = map_json_type_to_ts(field_schema)
        
        return [
            f"export function create{name}({field_name}: {ts_type}): {name} {{",
            f"  return {{ {field_name} }};",
            "}\n"
        ]

    # We determine if the argument object itself should be optional.
    # If EVERY field in the model is optional, the whole argument is optional.

    is_entire_model_optional = True
    for field_name, field_schema in props.items():
        # A field is 'truly required' if it's in the required list 
        # AND isn't a constant (like 'name').
        is_const = "const" in field_schema or ("enum" in field_schema and len(field_schema["enum"]) == 1)
        if field_name in required and not is_const:
            is_entire_model_optional = False
            break

    # Build the factory
    return [
        "/**",
        f" * Factory to create a typed {name} object.",
        " */",
        f"export function create{name}(fields{ '?' if is_entire_model_optional else '' }: {name}): {name} {{",
        # We spread the fields and ensure any 'fixed' values (like name: "delete_card") 
        # are applied last so they can't be accidentally overridden.
        f"  return {{ ...fields }};",
        "}\n"
    ]


def generate_typescript_definitions(models: typing.List[typing.Type[BaseModel]],
                                    output_dir: str):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, "server_types.ts")
    lines = [
        "// Auto-generated by utilities/align_channels.py",
        "// DO NOT EDIT THIS FILE MANUALLY",
        ""
    ]

    for model in models:
        s = model.model_json_schema()
        n = s.get("title", model.__name__).replace("[", "_").replace("]", "")
        r = set(s.get("required", []))

        # Now it's perfectly clear what is happening
        lines.extend(generate_interface(n, s, r))
        lines.extend(generate_factory(n, s))

# --- ADD THE NEW UNION EXPORTS AT THE BOTTOM ---
    def get_union_members(union_type):
        """Extracts class names from Union or Annotated[Union]"""
        origin = typing.get_origin(union_type)
        args = typing.get_args(union_type)
        if origin is typing.Annotated:
            return get_union_members(args[0])
        return [t.__name__.replace("[", "_").replace("]", "") for t in args]

    lines.append("/* --- Message Unions --- */")
    
    req_members = get_union_members(APIMessages)
    lines.append(f"export type APIMessages = {' | '.join(req_members)};")
    lines.append("")

    res_members = get_union_members(APIMessageResponses)
    lines.append(f"export type APIMessageResponses = {' | '.join(res_members)};")
    lines.append("")

    lines.append("/**")
    lines.append(" * Helper to cast a dictionary to a specific type.")
    lines.append(" */")
    lines.append("export function asType<T>(data: { [key: string]: any }): T {")
    lines.append("  return data as unknown as T;")
    lines.append("}")

    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    print(f"✅ Generated TypeScript definitions in {output_file}")


if __name__ == "__main__":
    found_models = get_messages()
    print(f"Found {len(found_models)} Pydantic models.")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_output_dir = os.path.join(project_root, FRONTEND_SCHEMA_DIR)

    generate_typescript_definitions(found_models, abs_output_dir)
