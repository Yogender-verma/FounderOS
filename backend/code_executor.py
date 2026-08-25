import sys
import os
import subprocess
import tempfile
import time
import json
from typing import Dict, Any, List, Optional

class CodeExecutor:
    """
    Modular Code Execution Engine.
    Executes candidate code against test cases with safety timeouts, stdout capture,
    and structured pass/fail results.
    Primary execution support: Python (MVP).
    Extensible handlers included for JavaScript, Java, and C++.
    """

    @staticmethod
    def run_code(language: str, code: str, custom_input: Optional[str] = None) -> Dict[str, Any]:
        lang = language.lower().strip()
        if lang == "python" or lang == "py":
            return CodeExecutor._run_python(code, custom_input)
        elif lang in ["javascript", "js", "node"]:
            return CodeExecutor._run_javascript(code, custom_input)
        elif lang == "java":
            return CodeExecutor._run_java(code, custom_input)
        elif lang in ["cpp", "c++", "c"]:
            return CodeExecutor._run_cpp(code, custom_input)
        else:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Unsupported language: {language}",
                "execution_time_ms": 0
            }

    @staticmethod
    def evaluate_submission(language: str, code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates candidate code against a list of test cases:
        [{"input": "...", "expected_output": "..."}, ...]
        """
        start_time = time.time()
        passed_count = 0
        total_count = len(test_cases)
        results = []

        for idx, tc in enumerate(test_cases):
            tc_input = str(tc.get("input", "")).strip()
            expected = str(tc.get("expected_output", "")).strip()
            
            # Format Python wrapper if needed to execute input -> print result
            exec_res = CodeExecutor._execute_with_test_input(language, code, tc_input)
            
            actual_output = exec_res.get("stdout", "").strip()
            err = exec_res.get("stderr", "").strip()

            # Compare clean output lines or strip trailing space
            is_passed = exec_res.get("success", False) and (actual_output == expected or actual_output.replace(" ", "") == expected.replace(" ", ""))
            if is_passed:
                passed_count += 1

            results.append({
                "test_case": idx + 1,
                "input": tc_input,
                "expected_output": expected,
                "actual_output": actual_output,
                "passed": is_passed,
                "error": err if not is_passed else None
            })

        elapsed_ms = int((time.time() - start_time) * 1000)
        overall_status = "PASSED" if passed_count == total_count and total_count > 0 else "FAILED"

        return {
            "status": overall_status,
            "test_cases_passed": passed_count,
            "total_test_cases": total_count,
            "pass_rate_percent": round((passed_count / total_count * 100), 1) if total_count > 0 else 0,
            "execution_time_ms": elapsed_ms,
            "test_results": results
        }

    @staticmethod
    def _run_python(code: str, custom_input: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            cmd = [sys.executable, temp_path]
            proc = subprocess.run(
                cmd,
                input=custom_input if custom_input else None,
                text=True,
                capture_output=True,
                timeout=3.0
            )
            elapsed_ms = int((time.time() - start) * 1000)
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "execution_time_ms": elapsed_ms
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Time Limit Exceeded (3.0s timeout)",
                "execution_time_ms": 3000
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution Error: {str(e)}",
                "execution_time_ms": 0
            }
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def _execute_with_test_input(language: str, code: str, tc_input: str) -> Dict[str, Any]:
        """
        Wraps code to inject tc_input if needed or executes directly via subprocess.
        """
        lang = language.lower().strip()
        if lang in ["python", "py"]:
            # Harness wrapper to execute top-level functions or standalone scripts
            harness = code + "\n\n"
            harness += "import sys, json\n"
            harness += "if __name__ == '__main__':\n"
            harness += "    tc_in = " + repr(tc_input) + "\n"
            harness += "    funcs = [v for k, v in list(globals().items()) if callable(v) and not k.startswith('_')]\n"
            harness += "    if 'solution' in globals() and callable(globals()['solution']):\n"
            harness += "        try:\n"
            harness += "            res = globals()['solution'](tc_in)\n"
            harness += "            if res is not None:\n"
            harness += "                print(res)\n"
            harness += "        except Exception:\n"
            harness += "            try:\n"
            harness += "                res = globals()['solution']()\n"
            harness += "                if res is not None:\n"
            harness += "                    print(res)\n"
            harness += "            except Exception as e:\n"
            harness += "                print(f'Error: {e}', file=sys.stderr)\n"
            harness += "    elif funcs:\n"
            harness += "        try:\n"
            harness += "            res = funcs[0](tc_in)\n"
            harness += "            if res is not None:\n"
            harness += "                print(res)\n"
            harness += "        except Exception as e:\n"
            harness += "            pass\n"

            return CodeExecutor._run_python(harness, custom_input=tc_input)
        
        elif lang in ["javascript", "js"]:
            return CodeExecutor._run_javascript(code, tc_input)
        else:
            return CodeExecutor.run_code(language, code, custom_input=tc_input)

    @staticmethod
    def _run_javascript(code: str, custom_input: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            cmd = ["node", temp_path]
            proc = subprocess.run(
                cmd,
                input=custom_input if custom_input else None,
                text=True,
                capture_output=True,
                timeout=3.0
            )
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "execution_time_ms": int((time.time() - start) * 1000)
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Node.js execution unavailable or failed: {str(e)}",
                "execution_time_ms": 0
            }
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def _run_java(code: str, custom_input: Optional[str] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Java execution toolchain reserved for production deployment. Python & JavaScript active.",
            "execution_time_ms": 0
        }

    @staticmethod
    def _run_cpp(code: str, custom_input: Optional[str] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "stdout": "",
            "stderr": "C++ execution toolchain reserved for production deployment. Python & JavaScript active.",
            "execution_time_ms": 0
        }
