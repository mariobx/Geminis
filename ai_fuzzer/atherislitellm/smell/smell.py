from radon.metrics import mi_visit
from ai_fuzzer.atherislitellm.logger.logs import log

def code_smells(python_code: str, threshold: float = 65.0, debug: bool = False) -> bool:
    """
    Determines if the given Python code smells based on the Maintainability Index (MI).
    Returns bool: True if the code smells, False otherwise.
    """
    try:
        results = mi_visit(python_code, True)
        if results is None:
            return False

        decision = results < threshold
        action = "fuzzing" if decision else "skipping"
        log(f"MI score: {results:.2f} ({action})", level="DEBUG", debug=debug)
        return decision
    except Exception as e:
        log(f"Error calculating code smells: {e}", level="ERROR")
        return True # Default to fuzzing if check fails
