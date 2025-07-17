from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent

GEMINIS_DIR = SRC_DIR / 'geminis'
OUTPUT_DIR = SRC_DIR / 'output_files'
LLM_DIR = GEMINIS_DIR / 'llm'
FETCH_DIR = GEMINIS_DIR / 'fetch'
PARSING_DIR = GEMINIS_DIR / 'parsing'
SANDBOX_DIR = GEMINIS_DIR / 'sandbox'

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
