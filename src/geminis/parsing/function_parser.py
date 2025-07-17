import os
import ast
from typing import List
from src.paths import *

def is_virtualenv_dir(path):
    """
    Returns True if the given directory looks like a Python virtual environment.
    """
    pyvenv_cfg = os.path.join(path, "pyvenv.cfg")
    bin_python = os.path.join(path, "bin", "python")
    scripts_python = os.path.join(path, "Scripts", "python.exe")

    if os.path.isfile(pyvenv_cfg):
        if os.path.isfile(bin_python) or os.path.isfile(scripts_python):
            return True
    return False

def get_python_file_paths(directory_path):
    """
    Recursively get .py files, skipping virtual environments.
    """
    python_files: List[str] = []
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if not is_virtualenv_dir(os.path.join(root, d))]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                python_files.append(full_path)
    return python_files

def extract_functions(path: str | Path) -> List[str]:
    """
    Parses a Python file and extracts all functions as source code strings.

    This function reads a file, parses it into an Abstract Syntax Tree (AST),
    and walks through the tree to find all function definitions.
    Does not execute any of the parsed code.

    Args:
        path: The absolute or relative path to the Python file.

    Returns:
        A list of strings, where each string is the source code of a
        class found in the file.
    """
    if not isinstance(path, (str, Path)) or not Path(path).is_file():
        return []

    source_code = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source_code, filename=str(path))

    functions = [
        ast.get_source_segment(source_code, node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    
    return [func for func in functions if func is not None]

def extract_classes(path: str | Path) -> List[str]:
    """
    Parses a Python file and extracts all classes as source code strings.

    This function reads a file, parses it into an Abstract Syntax Tree (AST),
    and walks through the tree to find all class definitions.
    Does not execute any of the parsed code.
    """
    if not isinstance(path, (str, Path)) or not Path(path).is_file():
        return []
    source_code = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source_code, filename=str(path))
    classes = [
        ast.get_source_segment(source_code, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]
    return [cls for cls in classes if cls is not None]

