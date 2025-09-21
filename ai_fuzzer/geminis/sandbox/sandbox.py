import subprocess
from pathlib import Path
import tempfile
import os
from textwrap import dedent
import venv
from ai_fuzzer.geminis.logger.logs import log

def save_to_file(name=None, text=None, path=None, debug=False):
    """Save provided text to a timestamped Atheris harness file in path."""

    if path is None:
        raise ValueError("The 'path' argument must not be None.")
    with open(os.path.join(path, f'atheris_harness_for_(({name})).py'), 'w') as f:
        f.write(text if text is not None else "")
        log(f"Text length: {len(text) if text else 0}", debug)
