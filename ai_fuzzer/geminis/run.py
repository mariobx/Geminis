from pathlib import Path
from datetime import datetime
from typing import Sequence, Dict
import os
from ai_fuzzer.geminis.llm import gem_request as atherisai
from ai_fuzzer.geminis.sandbox import sandbox
from ai_fuzzer.geminis.parsing import function_parser
from ai_fuzzer.geminis.smell.smell import code_smells
from ai_fuzzer.geminis.logger.logs import log

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
    log(f"Created run directory at: {run_dir} (type: {type(run_dir)})", debug)
    return run_dir

def retrieve_function_candidates(client, path: Path, prompt_id: str, prompt_yaml_path: Path, output_dir: Path, debug: bool = False, smell: bool = False) -> dict[str, str]:
    """Discover functions in the source path and generate test snippets via the LLM client.

    Functions may be filtered by code smell heuristics. Returns a mapping
    of function name to generated test code.
    """

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
                )
                block = atherisai.extract_code_blocks(response)
                func_tests[func_name] = block
                log(f"Generated test for function: {func_name}", debug)
        except Exception as e:
                log(f"Error processing file: {e}", debug)
                on_crash(output_dir, list(func_tests.values()), debug=debug)
    return func_tests

def retrieve_class_candidates(client, path: Path, prompt_id: str, prompt_yaml_path: Path, output_dir: Path, debug: bool = False, smell: bool = False) -> dict[str, str]:
    """Discover classes in the source path and generate test snippets via the LLM client.

    Classes may be filtered by code smell heuristics. Returns a mapping
    of class name to generated test code.
    """

    class_tests = {}
    pyfiles = function_parser.get_python_file_paths(path, debug=debug)
    if pyfiles:
        log(f"Retrieved {len(pyfiles)} Python files from: {path}", debug)
    for pyfile in pyfiles:
        classes = function_parser.extract_classes(pyfile, debug=debug)
        log(f"Found {len(classes)} classes in {pyfile}", debug)
        for clss_name, clss_body in classes.items():
            try:
                if smell:
                    if not code_smells(python_code=clss_body, debug=debug):
                        continue
                response = atherisai.get_response(
                    client=client,
                    prompt_id=prompt_id,
                    target_func=clss_body,
                    yaml_path=prompt_yaml_path,
                    debug=debug,
                )
                block = atherisai.extract_code_blocks(response)
                class_tests[clss_name] = block
            except Exception as e:
                log(f"Error processing class: {e}", debug)
                on_crash(output_dir, list(class_tests.values()), debug=debug)
    return class_tests

def run_function_testing(code_snippets: dict[str, str], output_base: Path, debug: bool):
    """Save generated function test snippets into a new timestamped run directory."""

    log(f"Creating function tests, total snippets: {len(code_snippets)}", debug)
    path = make_run_dir(output_base, debug=debug)
    for name, code in code_snippets.items():
        sandbox.save_to_file(name, code, path, debug=debug)

def run(
    source_dir: Path, output_dir: Path, prompt_id: str, mode: str, prompt_yaml_path: Path, api: str, debug: bool, smell: bool
) -> None:
    """Coordinate test generation: create client, generate snippets, and save them.

    Logs actions and selects either function- or class-based generation according
    to the `mode` argument.
    """

    log(f"run() called with mode={mode}, source_dir={source_dir}, output_dir={output_dir}, prompt_id={prompt_id}, prompt_yaml_path={prompt_yaml_path}", debug)

    client = atherisai.genai.Client(api_key=api)
    if mode == "functions":
        code_snippets = retrieve_function_candidates(client, source_dir, prompt_id, prompt_yaml_path, output_dir=output_dir, debug=debug, smell=smell)
    elif mode == "classes":
        code_snippets = retrieve_class_candidates(client, source_dir, prompt_id, prompt_yaml_path, output_dir=output_dir, debug=debug, smell=smell)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    run_function_testing(code_snippets, output_dir, debug=debug)
