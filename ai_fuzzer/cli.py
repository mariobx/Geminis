from pathlib import Path
import argparse
import os
import sys
import litellm
from ai_fuzzer.atherislitellm.run import run
from ai_fuzzer.atherislitellm.logger.logs import log, init_logger

def resolve_api_key(arg_val: str | None, model: str, debug: bool = False) -> str | None:
    """
    Resolve API key from CLI or Environment.
    If not found, use LiteLLM to tell the user which env var to set.
    """
    if arg_val:
        log("Using API key provided via CLI", debug)
        return arg_val.strip()

    try:
        check = litellm.validate_environment(model)
        if check.get("keys_in_environment"):
            log(f"Environment is valid for model '{model}'", debug)
            return None #LiteLLM will pick it up from env
        
        missing = check.get("missing_keys", [])
        if missing:
            print(f"Error: Missing API key for model '{model}'.")
            print("Please provide it via --api-key or set the following environment variable(s):")
            for key in missing:
                # Provide cross-platform instructions
                if sys.platform == "win32":
                    print(f"  set {key}=your_api_key_here")
                else:
                    print(f"  export {key}=your_api_key_here")
            sys.exit(1)
    except Exception as e:
        log(f"Error validating environment with LiteLLM: {e}", debug)
        sys.exit(1)
    
    return None

class ParseKwargs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            if '=' in value:
                key, val = value.split('=', 1)
                getattr(namespace, self.dest)[key] = val
            else:
                log(f"Warning: Ignoring malformed extra prompt: {value}", True)

def main():
    """Parse CLI arguments and run the fuzzer."""
    parser = argparse.ArgumentParser(description="AI-powered Python fuzzer with AtherisLiteLLM (LiteLLM + Atheris).")

    parser.add_argument("-s", "--src-dir", type=Path, required=True,
                        help="Path to the Python source directory to fuzz.")

    parser.add_argument("-o", "--output-dir", type=Path, required=True,
                        help="Where to store crash logs and generated harnesses.")

    parser.add_argument("-pp", "--prompts-path", type=Path, required=True,
                        help="Path to prompts.yaml config file.")

    parser.add_argument("-p", "--prompt", default="base", required=True,
                        help="Prompt ID from prompts.yaml to use (default: 'base')")

    parser.add_argument("-m", "--model", type=str, required=True,
                        help="LiteLLM model string (e.g., 'gemini/gemini-1.5-flash', 'openai/gpt-4').")

    parser.add_argument("-k", "--api-key", type=str,
                        help="API key string. If not provided, the tool will check environment variables.")

    parser.add_argument("-e", "--extra-model-prompts", nargs='*', action=ParseKwargs,
                        help="Extra vendor-specific parameters as key=value pairs (e.g., project=my-project).")

    parser.add_argument("-d", "--verbose", "-v", "--debug", action="store_true",
                        help="Enable debug/verbose mode.")

    parser.add_argument("-sm", "--smell", action="store_true",
                        help="Enable code smell filtering via Radon (Maintainability Index).")

    args = parser.parse_args()

    # Initialize logger early
    init_logger(args.output_dir)

    # Validate model
    try:
        litellm.get_llm_provider(args.model)
    except Exception as e:
        print(f"Error: '{args.model}' is not a recognized LiteLLM model. {str(e)}")
        sys.exit(1)

    # Resolve API Key
    api_key = resolve_api_key(args.api_key, args.model, args.verbose)
    if not api_key:
        print(f"Error: No API key found for model '{args.model}'. Please provide one via -k or environment variables.")
        sys.exit(1)

    # Prepare extra parameters
    extra_params = getattr(args, 'extra_model_prompts', {}) or {}
    if extra_params:
        log(f"Using extra model parameters: {list(extra_params.keys())}", args.verbose)

    try:
        run(
            source_dir=args.src_dir,
            output_dir=args.output_dir,
            prompt_id=args.prompt,
            prompt_yaml_path=args.prompts_path,
            model=args.model,
            api=api_key,
            debug=args.verbose,
            smell=args.smell,
            **extra_params
        )
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
