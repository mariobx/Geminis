import os
import sys
import traceback
import inspect
from pathlib import Path
from datetime import datetime

_LOG_BASE: Path | None = None
_LOG_FILE: Path | None = None

def init_logger(base_path: str) -> None:
    """Set up the log directory and log file under the given base path."""
    global _LOG_BASE, _LOG_FILE
    _LOG_BASE = Path(base_path)
    log_dir = _LOG_BASE / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    _LOG_FILE = log_dir / "log.log"

def log(msg: str, echo: bool = False) -> None:
    """Write a timestamped debug message to the log file (optionally echo)."""
    if _LOG_FILE is None:
        raise RuntimeError("Logger not initialized. Call init_logger(path) first.")

    # caller frame
    current = inspect.currentframe()
    frame = current.f_back if current is not None else None
    if frame is not None:
        filename = Path(frame.f_code.co_filename).name
        lineno = frame.f_lineno
    else:
        filename = "<unknown>"
        lineno = 0

    ts = datetime.now().strftime("%m/%d/%y %I:%M:%S%p")
    line = f"{ts} --- DEBUG --- {filename}:{lineno} - {msg}\n"

    # If called inside an exception handler, append traceback
    exc_info = sys.exc_info()
    if exc_info[0] is not None:
        line += "".join(traceback.format_exception(*exc_info)) + "\n"

    try:
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
        if echo:
            sys.stdout.write(line)
            sys.stdout.flush()
    except Exception as e:
        sys.stderr.write(f"[log_debug ERROR] {e}\n")
        sys.stderr.flush()