from pathlib import Path
from typing import Optional, Tuple
import yaml
from ai_fuzzer.geminis.fetch import fetch_docs
import re
from ai_fuzzer.geminis.logger.logs import log
import litellm

def extract_code_blocks(text):
    """Extract fenced code blocks from text and return them joined.

    Finds all triple-backtick code fences (optionally with a language
    tag) and returns their inner contents joined by two newlines. If
    no code blocks are found, returns an empty string.
    """
    if not text:
        return ""
    pattern = r'```(?:[\w+-]*)\s*\n([\s\S]*?)```'
    matches = re.findall(pattern, text)
    return '\n\n'.join(matches)

def load_prompt_data(prompt_id: str, yaml_path: Path, debug=False) -> Tuple[float, str, str]:
    """Load prompt settings from a YAML file and return (temperature, description, template)."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        all_prompts = yaml.safe_load(f)
    if prompt_id not in all_prompts:
        raise KeyError(f"Prompt ID '{prompt_id}' not found in {yaml_path}")
    entry = all_prompts[prompt_id]
    return float(entry["temperature"]), entry["description"], entry["template"]

def format_prompt(template: str, target_func: str, debug=False) -> str:
    """Fill the template with the target function and Atheris docs."""
    doc_block = f"{fetch_docs.fetch_atheris_readme(debug)}\n\n{fetch_docs.fetch_atheris_hooking_docs(debug)}"
    return template.replace("{{CODE}}", target_func).replace("{{DOCS}}", doc_block)

def get_response(client: dict, prompt_id: str, target_func: str, yaml_path: Path, debug: bool = False, **kwargs) -> str | None:
    """Prepare a prompt, call LLM via LiteLLM to generate content, and return the text."""
    log("Preparing prompt and making a LiteLLM call...", debug)
    
    try:
        temperature, _, template = load_prompt_data(prompt_id, yaml_path, debug)
        full_prompt = format_prompt(template, target_func, debug)

        # LiteLLM handles retries via num_retries
        response = litellm.completion(
            model=client["model"],
            messages=[{"role": "user", "content": full_prompt}],
            api_key=client["api_key"],
            temperature=temperature,
            num_retries=5,
            **kwargs
        )

        content = getattr(getattr(getattr(response, "choices", [None])[0], "message", None), "content", None)
        if not content:
            log("Warning: Received empty content from model response.", True)
        return content

    except Exception as e:
        log(f"Error during LLM completion: {e}", True)
        return None
