## AtherisLiteLLM:
This project creates a LLM-assisted Python fuzzing harness generator designed to leverage large language models via LiteLLM to automatically build fuzzing harnesses for target Python functions and classes. It uses Google’s Atheris fuzzing engine to dynamically generate and test code, with the aim of uncovering bugs or vulnerabilities in software.

# Usage:
  geminis \
    --src-dir /path/to/code \
    --output-dir /path/to/logs \
    --model google/gemini-1.5-flash \
    --prompts-path /path/to/prompts.yaml \
    --prompt base \
    --api-key your_api_key_here (optional if env var is set) \
    --extra-model-prompts project=my-project \
    --debug \
    --smell

# Arguments:
  - `-s`, `--src-dir`: Path to the Python source directory to fuzz.
  - `-o`, `--output-dir`: Where to store crash logs and generated harnesses.
  - `-m`, `--model`: LiteLLM model string (e.g., `gemini/gemini-1.5-flash`, `openai/gpt-4`).
  - `-pp`, `--prompts-path`: Path to `prompts.yaml` config file.
  - `-p`, `--prompt`: Prompt ID from `prompts.yaml` to use (default: `base`).
  - `-k`, `--api-key`: API key string (optional if environment variable is set).
  - `-e`, `--extra-mode-prompts`: Extra vendor-specific parameters as `key=value` pairs.
  - `-d`, `--debug`: Enable debug/verbose mode.
  - `-sm`, `--smell`: Enable code smell filtering via Radon.

# Workflow:
  1. Resolve API key (environment variable or raw string) and verify model via LiteLLM.
  2. Discover .py files; parse target functions and classes.
  3. (Optional) Filter by maintainability index using Radon.
  4. Build prompt with Atheris docs + target code; send to the LLM via LiteLLM.
  5. Save generated harnesses into a timestamped run directory.
