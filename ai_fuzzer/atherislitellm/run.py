from pathlib import Path
from datetime import datetime
from typing import Sequence, Dict
import os
from ai_fuzzer.atherislitellm.llm import llm_requests as atherisai
from ai_fuzzer.atherislitellm.sandbox import sandbox
from ai_fuzzer.atherislitellm.parsing import function_parser
from ai_fuzzer.atherislitellm.smell.smell import code_smells
from ai_fuzzer.atherislitellm.logger.logs import log

def on_crash(output_dir: Path, data: list, debug: bool = False) -> None:
    """Write a crash report file containing harness outputs and log the event."""

    try:
        log(f"Crash occurred, output directory: {output_dir}", debug)
        with open(output_dir / "crash_report.txt", "w", encoding="utf-8") as f:
            for i, contents in enumerate(data):
                f.write(f"HARNESS {i+1}\n\n----\n\n{contents}\n\n----\n\n")
    except (OSError, IOError, Exception) as e:
        log(f"Failed to write crash report: {e}", debug)

def make_run_dir(base: Path, debug=False) -> Path:
    """Create and return a timestamped run directory under the given base path."""

    timestamp = datetime.now().strftime("%m-%d-%y_%I-%M-%S%p").lower()
    run_dir = base / f"run-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    log(f"Created run directory at: {run_dir}", debug)
    return run_dir

def retrieve_function_candidates(client: dict, path: Path, prompt_id: str, prompt_yaml_path: Path, output_dir: Path, run_dir: Path, debug: bool = False, smell: bool = False, **kwargs) -> dict[str, str]:
    """Discover functions in the source path and generate test snippets via the LLM client."""

    func_tests = {}
    pyfiles = function_parser.get_python_file_paths(path, debug=debug)
    if pyfiles:
        log(f"Retrieved {len(pyfiles)} Python files from: {path}", debug)
    for pyfile in pyfiles:
        try:
            funcs = function_parser.extract_functions(pyfile, debug=debug)
            log(f"Found {len(funcs)} functions in {pyfile}", debug)
            for func_name, func_body in funcs.items():
                if smell:
                    if not code_smells(python_code=func_body, debug=debug):
                        continue
                response = atherisai.get_response(
                    client=client,
                    prompt_id=prompt_id,
                    target_func=func_body,
                    yaml_path=prompt_yaml_path,
                    debug=debug,
                    **kwargs
                )
                block = atherisai.extract_code_blocks(response)
                func_tests[func_name] = block
                log(f"Generated test for function: {func_name}", debug)
                
                # Save immediately
                sandbox.save_to_file(func_name, block, run_dir, debug=debug)
        except Exception as e:
                log(f"Error processing file: {e}", debug)
                on_crash(output_dir, list(func_tests.values()), debug=debug)
    return func_tests

def retrieve_class_candidates(client: dict, path: Path, prompt_id: str, prompt_yaml_path: Path, output_dir: Path, run_dir: Path, debug: bool = False, smell: bool = False, **kwargs) -> dict[str, str]:
    """Discover classes in the source path and generate test snippets via the LLM client."""

    class_tests = {}
    pyfiles = function_parser.get_python_file_paths(path, debug=debug)
    if pyfiles:
        log(f"Retrieved {len(pyfiles)} Python files from: {path}", debug)
    for pyfile in pyfiles:
        classes_in_file, functions_inside_classes = function_parser.extract_classes(pyfile, debug=debug)
        log(f"Found {len(classes_in_file)} classes in {pyfile}", debug)
        try:
            for class_name, class_body in classes_in_file.items():
                if smell:
                    if not code_smells(python_code=class_body, debug=debug):
                        continue
                methods = functions_inside_classes.get(class_name, []) 
                for function_name, function_body in methods:
                    customized_target_prompt = (
                        f"\n\n{class_body}\n\n"
                        f"**FUZZING FOCUS**\n"
                        f"Method Name: {function_name}\n"
                        f"Method Body:\n{function_body}"
                    )
                    response = atherisai.get_response(
                        client=client,
                        prompt_id=prompt_id,
                        target_func=customized_target_prompt,
                        yaml_path=prompt_yaml_path,
                        debug=debug,
                        **kwargs
                    )
                    block = atherisai.extract_code_blocks(response)
                    key = f"{class_name}.{function_name}"
                    class_tests[key] = block
                    log(f"Generated test for class method: {key}", debug)
                    
                    # Save immediately
                    sandbox.save_to_file(key, block, run_dir, debug=debug)
        except Exception as e:
            log(f"Error processing class: {e}", debug)
            on_crash(output_dir, list(class_tests.values()), debug=debug)
    return class_tests

def save_harnesses(code_snippets: dict[str, str], run_dir: Path, debug: bool):
    """Save generated harnesses into the provided run directory (Redundant but kept for compatibility)."""
    if not code_snippets:
        return
    log(f"Saving {len(code_snippets)} harnesses to {run_dir}", debug)
    for name, code in code_snippets.items():
        if code:
            sandbox.save_to_file(name, code, run_dir, debug=debug)

def run(
        source_dir: Path, output_dir: Path, prompt_id: str, prompt_yaml_path: Path, model: str, api: str | None, debug: bool, smell: bool, **kwargs
) -> None:
    """Coordinate test generation: create client, generate snippets, and save them immediately."""

    log(f"run() called with source_dir={source_dir}, output_dir={output_dir}, model={model}, prompt_id={prompt_id}", debug)

    client = {
            "model": model.strip() if model else "",
            "api_key": api.strip() if api else None,
    }

    # Ensure output_dir exists
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = make_run_dir(output_dir, debug=debug)

    log(f"Starting candidate retrieval for functions from {source_dir}", debug)
    function_code_snippets = retrieve_function_candidates(client, source_dir, prompt_id, prompt_yaml_path, output_dir=output_dir, run_dir=run_dir, debug=debug, smell=smell, **kwargs)
    log(f"Found {len(function_code_snippets)} function snippets", debug)

    log(f"Starting candidate retrieval for classes from {source_dir}", debug)
    class_code_snippets = retrieve_class_candidates(client, source_dir, prompt_id, prompt_yaml_path, output_dir=output_dir, run_dir=run_dir, debug=debug, smell=smell, **kwargs)
    log(f"Found {len(class_code_snippets)} class snippets", debug)

    log(f"Run completed. All harnesses saved in {run_dir}", debug)
