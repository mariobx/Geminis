import os
import ast
from typing import List
from pathlib import Path
from ai_fuzzer.geminis.logger.logs import log

def is_virtualenv_dir(path, debug=False):
    """
    Returns True if the given directory looks like a Python virtual environment.
    """
    pyvenv_cfg = os.path.join(path, "pyvenv.cfg")
    bin_python = os.path.join(path, "bin", "python")
    scripts_python = os.path.join(path, "Scripts", "python.exe")
    if os.path.isfile(pyvenv_cfg):
        if os.path.isfile(bin_python) or os.path.isfile(scripts_python):
            log(f"Found virtualenv at {path}, which we will ignore", debug)
            return True
    return False

def get_python_file_paths(directory_path, debug=False):
    """
    Recursively get .py files, skipping virtual environments.
    """
    log(f"Walking directory {directory_path} (type: {type(directory_path)})", debug)
    python_files: List[str] = []
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if not is_virtualenv_dir(os.path.join(root, d), debug)]
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                python_files.append(full_path)
                log(f"Found Python file: {full_path} (type: {type(full_path)})", debug)
    return python_files

def extract_functions(path: str | Path, debug=False) -> dict[str, str]:
    """
    Parses a Python file and extracts all functions as a dictionary mapping function names to source code strings.
    """
    path = Path(path)
    if not path.is_file():
        return {}

    source_code = path.read_text(encoding="utf-8")
    tree = ast.parse(source_code, filename=str(path))

    # Iterate ONLY through the top-level nodes of the file
    # This automatically excludes functions defined inside classes
    functions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            source = ast.get_source_segment(source_code, node)
            if source:
                functions[node.name] = source

    log(f"Extracted {len(functions)} top-level function(s) from {path}", debug)
    return functions

def extract_classes(path: str | Path, debug=False):
    path = Path(path)
    if not path.is_file():
        return {}, {}

    source_code = path.read_text(encoding="utf-8")
    tree = ast.parse(source_code)

    classes_in_file = {}
    functions_inside_classes = {}

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            cls_name = node.name
            cls_body = ast.get_source_segment(source_code, node)
            classes_in_file[cls_name] = cls_body
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_source = ast.get_source_segment(source_code, item)
                    methods.append((item.name, method_source))
            
            functions_inside_classes[cls_name] = methods

    log(f"Extracted {len(classes_in_file)} class(es) from {path}", debug)
    return classes_in_file, functions_inside_classes
