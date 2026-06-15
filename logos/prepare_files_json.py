import json
import os

files_to_push = [
    "VOID_LOGOS_LANGUAGE_SPEC.md",
    "__init__.py",
    "compiler.py",
    "exceptions.py",
    "lexer.py",
    "logos_ast.py",
    "parser.py",
    "test_logos.py",
    "generate_dataset.py",
    "logos_intent_dataset.jsonl"
]

files_array = []
logos_dir = "logos"

for fname in files_to_push:
    fpath = os.path.join(logos_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    files_array.append({
        "path": f"logos/{fname}",
        "content": content
    })

output_payload = {
    "owner": "DaVoidArchitect",
    "repo": "VoidOS",
    "branch": "main",
    "message": "Implement Logos vocabulary expansion, compiler validation, and Phase 2 dataset generation",
    "files": files_array
}

scratch_dir = "scratch"
if not os.path.exists(scratch_dir):
    os.makedirs(scratch_dir)

output_path = os.path.join(scratch_dir, "push_payload.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"Successfully prepared push payload in '{output_path}'. Size: {os.path.getsize(output_path)} bytes.")
