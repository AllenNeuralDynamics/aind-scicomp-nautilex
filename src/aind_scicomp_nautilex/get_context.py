import os
import ast
import inspect
from pydantic import BaseModel, Field

def _extract_fields_from_class_node(node):
    """Helper function to extract fields from a class AST node."""
    fields = []
    for subnode in node.body:
        if isinstance(subnode, ast.AnnAssign):
            field_name = subnode.target.id
            field_type = ast.unparse(subnode.annotation)

            # Extract field constraints if using Field(...)
            default_value = ""
            if subnode.value and isinstance(subnode.value, ast.Call):
                if isinstance(subnode.value.func, ast.Name) and subnode.value.func.id == "Field":
                    args = [ast.unparse(arg) for arg in subnode.value.args]
                    kwargs = {kw.arg: ast.unparse(kw.value) for kw in subnode.value.keywords}
                    if args or kwargs:
                        default_value = f" (default={', '.join(args)}, {', '.join(f'{k}={v}' for k, v in kwargs.items())})"

            fields.append(f"{field_name}: {field_type}{default_value}")
    return fields

def extract_pydantic_models_from_file(filepath):
    """Extracts all classes from a Python file."""
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)

    models = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            model_name = node.name
            fields = _extract_fields_from_class_node(node)
            if fields:  # Only add classes that have annotated fields
                models.append((model_name, fields))

    return models

def extract_top_level_pydantic_models_from_file(filepath):
    """Extracts only top-level classes from a Python file, excluding those starting with underscore."""
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)

    models = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            # Skip if class name starts with underscore
            if node.name.startswith('_'):
                continue
            # Skip if class inherits from anything other than BaseModel
            if node.bases and len(node.bases) == 1:
                base = node.bases[0]
                if not (isinstance(base, ast.Name) and base.id == "BaseModel"):
                    continue
                    
            model_name = node.name
            fields = _extract_fields_from_class_node(node)
            if fields:  # Only add classes that have annotated fields
                models.append((model_name, fields))

    return models


def flatten_pydantic_models(src_folder, get_all_models: bool):
    """Recursively find and extract Pydantic models from a folder."""
    all_models = []
    for root, _, files in os.walk(src_folder):
        for file in files:
            if file.endswith(".py") and not "__init__" in file and not "utils" in file:
                filepath = os.path.join(root, file)
                if get_all_models:
                    models = extract_pydantic_models_from_file(filepath)
                else:
                    models = extract_top_level_pydantic_models_from_file(filepath)
                all_models.extend(models)

    # Format output for LLM context
    output = []
    for model_name, fields in all_models:
        output.append(f"Model: {model_name}\n" + "\n".join(f"  - {field}" for field in fields))
    return "\n\n".join(output)

if __name__ == "__main__":

    src_folder = "/Users/dan/proj/aind/aind-data-schema/src/aind_data_schema/"  # Adjust if your schema folder is located elsewhere
    schema_context = flatten_pydantic_models(src_folder, True)
    with open("/Users/dan/proj/aind/aind-scicomp-nautilex/src/aind_scicomp_nautilex/schema_context.txt", "w", encoding="utf-8") as f:
        f.write(schema_context)  
    print("Wrote aind-data-schema context")

    src_folder = "/Users/dan/proj/aind/aind-data-schema-models/src/aind_data_schema_models/"  # Adjust if your schema folder is located elsewhere
    schema_context = flatten_pydantic_models(src_folder, False)
    with open("/Users/dan/proj/aind/aind-scicomp-nautilex/src/aind_scicomp_nautilex/models_context.txt", "w", encoding="utf-8") as f:
        f.write(schema_context)  
    print("Wrote aind-data-schema-models context")
