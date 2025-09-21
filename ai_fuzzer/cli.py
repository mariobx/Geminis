from pathlib import Path
import argparse
from ai_fuzzer.geminis.run import run
import os
import requests
from ai_fuzzer.geminis.logger.logs import log, init_logger


def get_key_from_env(debug: bool = False) -> str | None:
    """Return an API key from the GENAI_API_KEY environment variable if present."""
    if env_key := os.getenv("GENAI_API_KEY"):
        log("Using API key from environment variable", debug)
        return env_key.strip()
    return None

def get_key_from_file(path_str: str, debug: bool = False) -> str | None:
    """Read and return an API key from a text file, or None on error."""
    try:
        content = Path(path_str).read_text(encoding="utf-8")
        log(f"API key loaded from file: {path_str}", debug)
        return content.strip()
    except IOError as e:
        print(f"Error reading API key file '{path_str}': {e}")
        return None

def get_key_from_string(key_str: str, debug: bool = False) -> str:
    """Treat the provided string as the API key and return it trimmed."""
    log("Using API key passed as a literal string", debug)
    return key_str.strip()

def verify_key(key: str, debug: bool = False) -> bool:
    """Check whether the provided API key is valid by calling the Google endpoint."""
    log("Verifying API key...", debug)
    url = "https://generativelanguage.googleapis.com/v1/models"
    headers = {"x-goog-api-key": key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            log("API key verified successfully.", debug)
            return True
        else:
            print(f"API key verification failed (status: {resp.status_code})")
            return False
    except requests.RequestException as e:
        print(f"Error during API key verification: {e}")
        return False

def resolve_api_key(arg_val: str | None, debug: bool = False) -> str:
    """Locate and verify the API key from env, file path, or literal string."""
    key = None

    key = get_key_from_env(debug)

    if not key and arg_val:
        if Path(arg_val).is_file():
            key = get_key_from_file(arg_val, debug)
        else:
            key = get_key_from_string(arg_val, debug)

    if not key:
        print("No API key provided. Use --api-key or set GENAI_API_KEY.")
        exit(1)

    if not verify_key(key, debug):
        exit(1)

    return key



def main():
    """Parse CLI arguments and run the fuzzer with the resolved API key."""
    parser = argparse.ArgumentParser(description="AI-powered Python fuzzer with Gemini + Atheris.")

    parser.add_argument("--src-dir", type=Path, required=True,
                        help="Path to the Python source directory to fuzz.")

    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Where to store crash logs.")

    parser.add_argument("--prompts-path", type=Path, required=True,
                        help="Path to prompts.yaml config file (default: geminis/llm/prompts.yaml)")

    parser.add_argument("--prompt", default="base", required=True,
                        help="Prompt ID from prompts.yaml to use (default: 'base')")

    parser.add_argument("--mode", choices=["functions", "classes"], default="functions",
                        help="Target fuzzing of functions or classes, default is functions")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode to print internal states.")
    parser.add_argument("--api-key", type=str,
                        help="API key string or path to file containing it. This can be the api key itself, a path to the api as a single line txt file, or setting the enviorment variable GEMINI_API_KEY with bash: export GEMINI_API_KEY=<YOUR_API_KEY_HERE>")
    parser.add_argument("--smell", action="store_true",
                        help="Enable code smell to judge programatically if code should be fuzzed.")

    args = parser.parse_args()
    output_dir = args.output_dir
    init_logger(output_dir)
    api_key=resolve_api_key(args.api_key, args.debug)

    try:
        run(
            source_dir=args.src_dir,
            output_dir=output_dir,
            prompt_id=args.prompt,
            mode=args.mode,
            prompt_yaml_path=args.prompts_path,
            debug=args.debug,
            api=api_key,
            smell=args.smell
        )
    except Exception as e:
        import traceback
        print("ERROR:", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
