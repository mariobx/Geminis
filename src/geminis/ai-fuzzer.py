import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from llm import gem_request as atherisai
from fetch import fetch_docs as docs
from sandbox import sandbox
from datetime import datetime
from parsing import function_parser
from typing import Sequence, Tuple

def make_run_dir(base: Path = Path("runs")) -> Path:
    timestamp = datetime.now().strftime("%m-%d-%y_%H-%M-%S")
    run_dir = base / f"run-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir

def retrieve_function_candidates(path: str | Path | os.PathLike) -> Sequence[str]:
    """Return func_tests generated from all .py files under *path*."""
    path = Path(path)  # normalize
    func_tests: list[str] = []

    for pyfile in function_parser.get_python_file_paths(path):
        for func in function_parser.extract_functions(pyfile):
            func_tests.append(atherisai.extract_code_blocks(atherisai.get_response(target_func=func)))

    return func_tests



def retrieve_class_candidates(path: str | Path | os.PathLike) -> Sequence[str]:
    """Return class_tests generated from all .py files under *path*."""
    path = Path(path)  # normalize
    class_tests: list[str] = []

    for pyfile in function_parser.get_python_file_paths(path):
        for clss in function_parser.extract_classes(pyfile):
            class_tests.append(atherisai.get_response(target_func=clss))

    return class_tests

def run_function_testing(list_of_code: Sequence[str]):
    for code in list_of_code:
        path = make_run_dir(Path(os.path.join(os.getcwd(), '../output_files')))
        sandbox.save_to_file(code, path)
        sandbox.sandbox_venv(code, path)

print('bye')
run_function_testing(retrieve_function_candidates(path='/home/mario/Work/personal/fuzz/src/geminis/parsing/'))