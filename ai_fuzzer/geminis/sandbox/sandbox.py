import subprocess
from pathlib import Path
import tempfile
import os
from textwrap import dedent
import venv
from ai_fuzzer.geminis.logger.logs import log

def save_to_file(name=None, text=None, path=None, debug=False):
    """Save provided text to a timestamped Atheris harness file in path,
    creating a subdirectory named after `name` and placing the file inside it.
    """
    if path is None:
        raise ValueError("The 'path' argument must not be None.")

    # Make subdirectory: <path>/<name>/
    subdir = os.path.join(path, str(name))
    os.makedirs(subdir, exist_ok=True)

    # Write file inside the subdirectory
    file_path = os.path.join(subdir, f'atheris_harness_for_(({name})).py')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text if text is not None else "")

    log(f"Text length: {len(text) if text else 0}", debug)

