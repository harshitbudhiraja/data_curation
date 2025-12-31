from openai import OpenAI
import subprocess
import tempfile
import re
import pytest
# client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")


def extract_python_code(llm_response: str) -> str:
    """Extract code if wrapped in <python> tags or ```python code block. Otherwise return as is."""
    llm_response_strip = llm_response.lstrip()
    # Check <python> tag
    if llm_response_strip.startswith("<python>"):
        match = re.search(r"<python>(.*?)</python>", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            # Just strip the tag start if no end tag
            return llm_response_strip.replace("<python>", "", 1).strip()
    # Check triple-backtick python code block
    elif llm_response_strip.startswith("```python"):
        match = re.search(r"```python(.*?)```", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            # Just remove the leading code fence
            return llm_response_strip[len("```python"):].strip()
    elif llm_response_strip.startswith("```"):
        # fence with no python, just ``` ?
        match = re.search(r"```(.*?)```", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            return llm_response_strip.replace("```", "", 1).strip()
    else:
        return llm_response_strip

def run_python_code(llm_response: str, test_cases: list) -> dict:
    """Extract and execute Python code from LLM response and run unit tests."""
    try:
        code = extract_python_code(llm_response)


        if not code or not any(keyword in code for keyword in ['def ', 'class ', 'import ', '=', 'print', 'if ', 'for ', 'while ']):
            return {
                "success": False,
                "error_type": "invalid_code",
                "message": "No valid Python code found in response",
                "code_output": "",
                "test_results": ""
            }
            
        # Add test cases to the code
        test_code = code + "\n\n"
        for i, test in enumerate(test_cases):
            test_code += f"def test_{i}():\n    {test}\n\n"
            
        # Execute the code with tests
        with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False) as f:
            f.write(test_code)
            f.flush()
            
            # Run the code
            result = subprocess.run(
                ["python3", f.name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Run the tests
            test_result = subprocess.run(
                ["python3", "-m", "pytest", f.name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            code_output = result.stdout or result.stderr
            test_output = test_result.stdout or test_result.stderr
            
            # Check if tests passed
            tests_passed = test_result.returncode == 0
            
            return {
                "success": tests_passed,
                "error_type": "test_failure" if not tests_passed else None,
                "message": "Tests failed" if not tests_passed else "All tests passed",
                "code_output": code_output,
                "test_results": test_output
            }
            
    except Exception as e:
        return {
            "success": False,
            "error_type": "execution_error",
            "message": f"Error: {e}",
            "code_output": "",
            "test_results": ""
        }


code_str = """
<python>\nimport re\n\ndef find_char_long(text):\n    pattern = r'\\b\\w{4,}\\b'  # Raw string to prevent escape issues\n    return re.findall(pattern, text, re.IGNORECASE)\n\nprint(find_char_long(\"apple banana cat\"))\nprint(find_char_long(\"hello_world\"))\nprint(find_char_long(\"Apple banana CAT\"))\n</python>\nThis code uses a raw string (prefixed with 'r') to define the regex pattern, which prevents the need for backslash escaping. The pattern '\\b\\w{4,}\\b' matches word boundaries around words with at least 4 characters, and re.IGNORECASE is used to ignore case sensitivity. It should now correctly filter out \"cat\" and \"hello_world\" while handling case differences.\n<|fim_middle|>"""

test_cases =["assert find_char_long('Please move back to stream') == ['Please', 'move', 'back', 'stream']", "assert find_char_long('Jing Eco and Tech') == ['Jing', 'Tech']", "assert find_char_long('Jhingai wulu road Zone 3') == ['Jhingai', 'wulu', 'road', 'Zone']"]

result = run_python_code(code_str, test_cases)
# print(result)
# print(f"Success: {result['success']}")
# print(f"Error Type: {result['error_type']}")
# print(f"Message: {result['message']}")
# print(f"Code Output:\n{result['code_output']}")
# print(f"Test Results:\n{result['test_results']}")