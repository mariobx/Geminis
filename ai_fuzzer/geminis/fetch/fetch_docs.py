import re
import backoff
import requests
from ai_fuzzer.geminis.logger.logs import log

cache = {}

RETRYABLE_EXCEPTIONS = (
    requests.exceptions.RequestException,
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError
)

def is_bad_response(docs: str) -> bool:
    """Return True when the fetched documentation text is empty or None."""
    if not docs:
        # The response is None or "", which is considered a failure.
        log("A response error occurred (empty/missing text). Retrying...", True)
        return True

    return False #success


@backoff.on_predicate(backoff.expo, predicate=is_bad_response, max_tries=5, jitter=backoff.full_jitter)
@backoff.on_exception(backoff.expo, RETRYABLE_EXCEPTIONS, max_tries=5, jitter=backoff.full_jitter)
def fetch_atheris_readme(debug: bool = False) -> str:
    """Fetch and return Google's Atheris README as cleaned plain text.

    The returned string is cached to avoid repeated network calls.
    """

    if "readme" in cache:
        return cache["readme"]

    url = "https://raw.githubusercontent.com/google/atheris/master/README.md"

    response = requests.get(url, timeout=8)
    response.raise_for_status()

    content = response.text
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    content = re.sub(r'\[.*?\]\(https?:\/\/.*?\)', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    formatted = f"""
==== START OF ATHERIS DOCUMENTATION ====

This is the official README documentation for Google's Atheris fuzzing framework for Python.

{content}

==== END OF ATHERIS DOCUMENTATION ====
"""
    cache["readme"] = formatted
    log("fetched atheris readme", debug)
    return formatted


@backoff.on_exception(backoff.expo, RETRYABLE_EXCEPTIONS, max_tries=5, jitter=backoff.full_jitter)
@backoff.on_predicate(backoff.expo, predicate=is_bad_response, max_tries=5, jitter=backoff.full_jitter)
def fetch_atheris_hooking_docs(debug=False):
    """Fetch and return Google's Atheris hooking docs as cleaned plain text.

    The returned string is cached to avoid repeated network calls.
    """

    if "hooking" in cache:
        return cache["hooking"]

    url = "https://raw.githubusercontent.com/google/atheris/refs/heads/master/hooking.md"
    
    response = requests.get(url, timeout=8)
    response.raise_for_status()

    content = response.text
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    content = re.sub(r'\[.*?\]\(https?:\/\/.*?\)', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    formatted = f"""
==== START OF ATHERIS' HOOKING DOCUMENTATION ====

This is the official README documentation for Google's Atheris fuzzing framework for Python.

{content}

==== END OF ATHERIS' HOOKING DOCUMENTATION ====
"""
    cache["hooking"] = formatted
    log("fetched atheris hooking documentation", debug)
    return formatted