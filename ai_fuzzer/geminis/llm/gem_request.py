import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple
import google.genai as genai
import yaml
from google.genai.types import GenerateContentConfig
from ai_fuzzer.geminis.fetch import fetch_docs
import re
from ai_fuzzer.geminis.logger.logs import log
import backoff


def extract_code_blocks(text):
    """Extract fenced code blocks from text and return them joined.

    Finds all triple-backtick code fences (optionally with a language
    tag) and returns their inner contents joined by two newlines. If
    no code blocks are found, returns an empty string.
    """

    pattern = r'```(?:[\w+-]*)\s*\n([\s\S]*?)```'
    matches = re.findall(pattern, text)
    return '\n\n'.join(matches)
    

def load_prompt_data(prompt_id: str, yaml_path: Path, debug=False) -> Tuple[float, str, str]:
    """Load prompt settings from a YAML file and return (temperature, description, template).

    Reads the YAML at `yaml_path`, looks up `prompt_id`, and returns a
    3-tuple: temperature (as float), a short description, and the
    prompt template string. Raises KeyError if the `prompt_id` is not
    present in the YAML file.
    """

    with open(yaml_path, "r", encoding="utf-8") as f:
        all_prompts = yaml.safe_load(f)
    if prompt_id not in all_prompts:
        raise KeyError(f"Prompt ID '{prompt_id}' not found in {yaml_path}")
    entry = all_prompts[prompt_id]
    return float(entry["temperature"]), entry["description"], entry["template"]


def format_prompt(template: str, target_func: str, debug=False) -> str:
    """Fill the template with the target function and Atheris docs.

    Fetches the Atheris README and hooking docs, inserts them into the
    template under the {{DOCS}} placeholder, and substitutes the
    target function source into {{CODE}}. Returns the completed prompt
    string ready for sending to the LLM.
    """

    doc_block = f"{fetch_docs.fetch_atheris_readme(debug)}\n\n{fetch_docs.fetch_atheris_hooking_docs(debug)}"
    return template.replace("{{CODE}}", target_func).replace("{{DOCS}}", doc_block)


def is_bad_response(response_text: str) -> bool:
    """Backoff predicate: return True when the LLM response is empty or missing.

    This is used by retry decorators to trigger another attempt when the
    model returns no text. A log entry is emitted when a bad response is
    detected.
    """

    if not response_text:
        # The response is None or "", which is considered a failure.
        log("A response error occurred (empty/missing text). Retrying...", True)
        return True

    return False #success


RETRYABLE_EXCEPTIONS = (
    genai.errors.ClientError, # type: ignore
    genai.errors.ServerError, # type: ignore
    genai.errors.APIError # type: ignore
)

@backoff.on_exception(backoff.expo, RETRYABLE_EXCEPTIONS, max_tries=5, jitter=backoff.full_jitter)
@backoff.on_predicate(backoff.expo, predicate=is_bad_response, max_tries=5, jitter=backoff.full_jitter)
def get_response(client, prompt_id: str, target_func: str, yaml_path: Path, debug: bool = False) -> str | None:
    """Prepare a prompt, call Gemini to generate content, and return the text.

    Loads the prompt template and temperature, composes the full prompt by
    inserting the target function and Atheris docs, then calls the Gemini
    model (`gemini-2.5-flash`) with a text-only response configuration. The
    retry and backoff behavior is implemented by the decorators applied to
    this function. Returns the generated text if present, otherwise None.
    """

    log("Preparing prompt and making a single API call attempt...", debug)
    temperature, _, template = load_prompt_data(prompt_id, yaml_path, debug)
    full_prompt = format_prompt(template, target_func, debug)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
        config=genai.types.GenerateContentConfig(response_modalities=['TEXT'], temperature=temperature)
    )
    
    return getattr(response, "text", None)

