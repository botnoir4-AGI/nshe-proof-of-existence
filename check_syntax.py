
import py_compile
import sys

try:
    py_compile.compile('orchestrator.py', doraise=True)
    print("OK: No syntax errors")
except py_compile.PyCompileError as e:
    print(f"ERROR: {e}")
