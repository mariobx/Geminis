
## Geminis: AI-Driven Python Fuzzing CLI

# Description:
This project creates a LLM-assisted Python fuzzing harness generator designed to leverage large language models like Gemini to automatically build fuzzing harnesses for target Python functions. It uses Google’s Atheris fuzzing engine to dynamically generate and test code, with the aim of uncovering bugs or vulnerabilities in software.
  
# Features:
  • AST parsing: Extract functions or classes from your code.
  • LLM harness gen: Embed code into prompts.yaml templates and call Gemini.
  • Optional smell filter: Skip high-maintainability code via Radon.
  • Isolated runs: Create venvs, execute harnesses, capture logs in timestamped folders.

# Usage:
  geminis \
    --src-dir /path/to/code \
    --output-dir /path/to/logs \
    --prompts-path /path/to/prompts.yaml \
    --api-key /path/to/api.txt \
    --prompt base \
    --mode functions \
    [--debug] \
    [--smell]

# Workflow:
  1. Load API key (env or file), verify model.
  2. Discover .py files; parse target snippets.
  3. (Optional) Filter by maintainability index.
  4. Build prompt with Atheris docs + code; send to Gemini.
  5. Create venv, write harness, run tests, save outputs.
