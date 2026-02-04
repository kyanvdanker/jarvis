import builtins
import cadquery as cq
import math
import cad_library
from cq_gears import SpurGear


def run_cad_code(code: str):
    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name not in ("cad_library", "cadquery"):
            raise ImportError(f"Import of '{name}' is not allowed")
        return __import__(name, globals, locals, fromlist, level)

    safe_globals = {
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "__import__": restricted_import,
        },
        "cq": cq,
        "cad_library": cad_library,
        "math": math,
    }

    local_vars = {}

    try:
        exec(code, safe_globals, local_vars)
    except Exception as e:
        return None, f"Execution error: {e}"

    build = local_vars.get("build")
    if not callable(build):
        return None, "build() not defined"

    try:
        result = build()
    except Exception as e:
        return None, f"build() failed: {e}"

    if not hasattr(result, "val"):
        return None, "build() did not return a CadQuery object"

    return result, None
