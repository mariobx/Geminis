import sys
from pathlib import Path
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import time
import os
import re
sys.path.append(str(Path(__file__).resolve().parent.parent))
from fetch import fetch_docs as docs

def extract_code_blocks(text):
    # Match content inside triple backticks, capture language tag but ignore it
    pattern = r'```(?:[\w+-]*)\s*\n([\s\S]*?)```'
    matches = re.findall(pattern, text)
    
    # Join multiple code blocks if needed
    return '\n\n'.join(matches)
    
def get_api() -> str:
    try:
        return str(open(os.path.join(os.getcwd(), 'llm/api.txt'), 'r').read())
    except FileNotFoundError:
        print("Error: api.txt not found. Please create this file and paste your API key in it.")
        sys.exit(1)

def get_response(contents = None, target_func = None):
    content_structure = f"""
You are an expert in software security and automated testing, specializing in fuzzing with Python's Atheris framework. Your task is to create a complete and runnable Python fuzzing harness for a target function that will be provided to you.

Follow these steps precisely:

**1. Analyze the Target Function:**
   - Examine the Python function provided below under "TARGET FUNCTION".
   - Identify the function's name and all of its input arguments.
   - Determine the expected data type for each argument (e.g., `string`, `integer`, `bytes`, `list of integers`).

**2. Plan the Fuzzing Strategy:**
   - Based on the argument types, determine the appropriate `FuzzedDataProvider` methods to use for generating each input (e.g., `fdp.ConsumeUnicode()`, `fdp.ConsumeInt()`, `fdp.ConsumeBytes()`, `fdp.ConsumeIntList()`).
   - The goal is to map the raw fuzzer data to the function's expected input signature.

**3. Generate the Fuzzing Harness Code:**
   - Write a single, self-contained Python script.
   - **Imports:** The script must import `atheris`, `sys`, and any other libraries required by the target function itself. You must ensure the ability to install these locally in the generated code, any package that is not python native needs to be installed in the generated code.  You can do this by creating the python code that actually uses the command pip install and then the package names setuptools, and wheel prior to atheris.
   - **Dependency Management:** At the very top of the script, do the actual `pip install` commands needed to run the code (e.g., `pip install atheris`, `pip install library-used-by-target`). Ensure you **INSTALL THE REQUIRED LIBRARIES** before **IMPORTING ANY NON NATIVE PYTHON PACKAGES**
   - **Target Function:** Include the complete target function code within the script so it is self-contained.
   - **Test Harness Function:** Define the core `TestOneInput(data)` function.
   - **Data Provider:** Inside `TestOneInput`, initialize the `atheris.FuzzedDataProvider(data)`.
   - **Input Generation:** Use the data provider to generate values for each of the target function's arguments according to your plan in step 2.
   - **Function Call:** Call the target function with the generated inputs inside a `try...except Exception` block. This is crucial for catching crashes and other errors.
   - **Logging and Data Persistence:**
   - **Create a crash-only logger by opening one log file at startup—os.open(path, O_WRONLY|O_CREAT|O_APPEND, 0o644)—and reusing that file descriptor globally. In TestOneInput, wrap the target code in a try/except, and on any exception base64-encode the input, build a single-line record (<epoch-ns>|<pid>|<b64>|<exception> \n), append it to a bytearray buffer, then exception so Atheris still registers the crash. When the buffer exceeds 64 KiB, flush with one os.write(fd, buf); also flush once more via an atexit handler. Give each worker its own file (exceptions.<pid>.log) to avoid contention, keep logs append-only and line-oriented, and use only os and base64—no dynamic configs, locks, or heavy libraries—to ensure zero impact on fuzzing throughput. Also ensure that a single crash does not stop the fuzzing.
   - **Atheris Setup:** After the function definitions, properly initialize Atheris with `atheris.Setup(sys.argv, TestOneInput)` and start the fuzzer with `atheris.Fuzz()`. Also ensure that you enable instrumentation in the atheris.Setup() with enable_python_coverage=True.

**4. Final Output:**
   - The final output must be ONLY the Python code in a single code block.
   - Do not provide explanations or text outside of the code block.
   - The code must be fully commented, explaining the logic of the harness, the input generation, and the error handling.

Before getting started, you must understand how the atheris tool works. Please understand read and understand the README before writing the harness.

{docs.fetch_atheris_readme()}

{docs.fetch_atheris_hooking_docs()}

---
**TARGET FUNCTION:**

{target_func}
---
    """
    client = genai.Client(api_key=get_api())

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=content_structure,
                config=GenerateContentConfig(response_modalities=['TEXT'], temperature=0.3)
            )
            print('got response')
            return response.text
        except genai.errors.ServerError as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)  # backoff delay
    raise RuntimeError("Failed after multiple attempts.")

