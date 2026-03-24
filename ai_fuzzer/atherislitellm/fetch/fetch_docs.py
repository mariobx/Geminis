import re
import requests
import time
from ai_fuzzer.atherislitellm.logger.logs import log

cache = {}

def fetch_with_retry(url: str, max_tries: int = 5, debug: bool = False) -> str:
    """Fetch URL with a simple retry mechanism."""
    for i in range(max_tries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            content = response.text
            if content:
                return content
            log(f"Empty response from {url}, retrying...", debug)
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            log(f"Error fetching {url}: {e}. Retrying ({i+1}/{max_tries})...", debug)
            if i < max_tries - 1:
                time.sleep(2 ** i) # Exponential backoff
    
    raise requests.exceptions.RequestException(f"Failed to fetch {url} after {max_tries} attempts")

def fetch_atheris_readme(debug: bool = False) -> str:
    """Fetch and return Google's Atheris README as cleaned plain text."""
    if "readme" in cache:
        return cache["readme"]

    url = "https://raw.githubusercontent.com/google/atheris/master/README.md"
    content = fetch_with_retry(url, debug=debug)

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

def fetch_atheris_hooking_docs(debug: bool = False) -> str:
    """Fetch and return Google's Atheris hooking docs as cleaned plain text."""
    if "hooking" in cache:
        return cache["hooking"]

    url = "https://raw.githubusercontent.com/google/atheris/refs/heads/master/hooking.md"
    content = fetch_with_retry(url, debug=debug)

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
