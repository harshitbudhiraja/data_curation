from openai import OpenAI
import subprocess
import tempfile
import re
import pytest
# client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")


def extract_python_code(llm_response: str) -> str:
    """Extract code if wrapped in <python> tags or ```python code block. Otherwise return as is."""
    llm_response_strip = llm_response.lstrip()
    
    # Check <python> tag - extract content between tags
    if "<python>" in llm_response:
        match = re.search(r"<python>(.*?)</python>", llm_response, re.DOTALL)
        if match:
            code = match.group(1).strip()
            # Remove any leading text before def/import/class
            code = re.sub(r'^.*?(?=(def |import |class |from |@))', '', code, flags=re.DOTALL)
            return code.strip()
    
    # Check triple-backtick python code block
    if "```python" in llm_response:
        match = re.search(r"```python(.*?)```", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # Check plain triple-backtick
    if "```" in llm_response:
        match = re.search(r"```(.*?)```", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # No tags found - try to extract code starting from def/import/class
    code_match = re.search(r'((?:def |import |class |from |@).*)', llm_response, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    
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
                "test_results": "",
                "tests_passed": 0
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
                ["venv/bin/python", f.name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Run the tests in a subprocess
            test_result = subprocess.run(
                ["venv/bin/python", "-m", "pytest", f.name, "-v"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            code_output = result.stdout or result.stderr
            test_output = test_result.stdout or test_result.stderr
            
            # Count how many tests passed
            passed_match = re.search(r'(\d+) passed', test_output)
            tests_passed_count = int(passed_match.group(1)) if passed_match else 0
            
            # Check if all tests passed
            all_tests_passed = test_result.returncode == 0
            
            return {
                "success": all_tests_passed,
                "error_type": "test_failure" if not all_tests_passed else None,
                "message": f"{tests_passed_count}/{len(test_cases)} tests passed" if not all_tests_passed else "All tests passed",
                "code_output": code_output,
                "test_results": test_output,
                "tests_passed": tests_passed_count
            }
            
    except Exception as e:
        return {
            "success": False,
            "error_type": "execution_error",
            "message": f"Error: {e}",
            "code_output": "",
            "test_results": "",
            "tests_passed": 0
        }


code_str = """
<python>\nimport re\n\ndef find_char_long(text):\n    pattern = r'\\b\\w{4,}\\b'  # Raw string to prevent escape issues\n    return re.findall(pattern, text, re.IGNORECASE)\n\nprint(find_char_long(\"apple banana cat\"))\nprint(find_char_long(\"hello_world\"))\nprint(find_char_long(\"Apple banana CAT\"))\n</python>\nThis code uses a raw string (prefixed with 'r') to define the regex pattern, which prevents the need for backslash escaping. The pattern '\\b\\w{4,}\\b' matches word boundaries around words with at least 4 characters, and re.IGNORECASE is used to ignore case sensitivity. It should now correctly filter out \"cat\" and \"hello_world\" while handling case differences.\n<|fim_middle|>"""

test_cases =["assert find_char_long('Please move back to stream') == ['Please', 'move', 'back', 'stream']", "assert find_char_long('Jing Eco and Tech') == ['Jing', 'Tech']", "assert find_char_long('Jhingai wulu road Zone 3') == ['Jhingai', 'wulu', 'road', 'Zone']"]

result = run_python_code(code_str, test_cases)
