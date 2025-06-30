import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from llm import gem_request as atherisai
from fetch import fetch_docs as docs
from sandbox import sandbox
from datetime import datetime

def make_run_dir(base: Path = Path("runs")) -> Path:
    timestamp = datetime.now().strftime("%m-%d-%y_%H-%M-%S")
    run_dir = base / f"run-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir

def format_output(response = None):
    return atherisai.extract_code_blocks(atherisai.get_response())

code = format_output()        

path = make_run_dir(Path(os.path.join(os.getcwd(), 'output_files')))
sandbox.save_to_file(code, path)
sandbox.sandbox_venv(code, path)

# print(fetch_atheris_readme())
