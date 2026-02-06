"""Tutor agent implementation adapted for data_curation."""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_calling import call_llm_openrouter
from langchain_core.messages import SystemMessage


# Bug injection removed - relying on natural difficulty of problems


def get_effort_level_prompt(turn_count: int) -> tuple:
    """Get effort level instruction and temperature based on turn count.
    
    Strategy:
    - Turns 1-2: Quick initial attempt (higher temp, less thorough)
    - Turns 3-4: Refinement based on feedback (medium temp, more focused)
    - Turns 5+: Careful complete solution (low temp, very thorough)
    
    Returns:
        tuple: (instruction_text, temperature)
    """
    if turn_count <= 2:
        # Early turns - quick first attempt
        instruction = """Provide a straightforward initial solution. Focus on the core logic without overthinking edge cases.
Write working code, but don't spend time on optimization or handling all corner cases yet."""
        temperature = 0.7
    elif turn_count <= 4:
        # Middle turns - refinement
        instruction = """Refine your solution based on the feedback. Address the specific issues mentioned.
Focus on fixing the errors while maintaining correct logic."""
        temperature = 0.5
    else:
        # Later turns - complete solution
        instruction = """Write a complete, production-quality solution that handles all edge cases and passes all tests.
Be thorough and careful with your implementation."""
        temperature = 0.3
    
    return instruction, temperature


# Load tutor system prompt from file
def load_tutor_prompt():
    """Load tutor system prompt from prompts folder."""
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'tutor_system_prompt.txt')
    with open(prompt_path, 'r') as f:
        return f.read()


def extract_code_only(response: str) -> str:
    """Aggressively extract only the Python code from response."""
    if not response:
        return ""
    
    # Remove think tags
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<think>.*', '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove common wrapper tags
    for tag in ['student', 'tutor', 'python', 'code', 'assistant', 'response']:
        response = re.sub(rf'<{tag}>\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(rf'\s*</{tag}>', '', response, flags=re.IGNORECASE)
    
    # Extract from markdown code blocks if present
    code_block_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    code_block_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
    if code_block_match:
        code = code_block_match.group(1).strip()
        # Only use if it looks like Python code
        if 'def ' in code or 'import ' in code:
            return code
    
    # Find the first 'def ' or 'import ' and extract from there
    # Stop at common non-code patterns
    code_start = re.search(r'((?:from |import |def |class |@)[^\n]*(?:\n(?:[ \t]+[^\n]*|\n))*)', response, re.MULTILINE)
    if code_start:
        code = code_start.group(1).strip()
        # Remove any trailing non-code text
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            # Stop if we hit explanation text
            if any(phrase in line.lower() for phrase in ['this function', 'this code', 'note:', 'example:', 'now write']):
                break
            clean_lines.append(line)
        return '\n'.join(clean_lines).strip()
    
    return response.strip()


def is_valid_code(text: str, function_name: str) -> bool:
    """Validate that output looks like proper Python code for the required function."""
    if not text or len(text) < 20:
        return False
    
    # Must contain the required function definition
    if function_name and f'def {function_name}' not in text:
        return False
    
    # Must have def keyword
    if 'def ' not in text:
        return False
    
    # Should not contain prompt leakage patterns
    bad_patterns = [
        'Write ONLY',
        'No explanations',
        'Now write code',
        'Example code:',
        'Function:',
        'Problem:',
        'user\n',
        'assistant\n',
    ]
    for pattern in bad_patterns:
        if pattern in text:
            return False
    
    return True


class TutorAgent:
    """Tutor agent that provides code solutions."""
    
    def __init__(self, model_name: str = "qwen/qwen2.5-coder-7b-instruct"):
        self.model_name = model_name
        self.system_prompt = load_tutor_prompt()
    
    def generate_response(self, conversation_history: list, problem: str = None, function_name: str = None, test_cases: list = None, turn_count: int = 0, execution_result: dict = None) -> str:
        """Generate tutor's response with code solution.
        
        Args:
            conversation_history: List of previous messages
            problem: The programming problem to solve
            function_name: Required function name
            test_cases: Test cases the code must pass
            turn_count: Current turn number (to adjust effort level)
            execution_result: Previous execution result if any
        
        Returns:
            Tutor's response as Python code
        """
        # Get effort level instruction and temperature based on turn count
        effort_instruction, temperature = get_effort_level_prompt(turn_count)
        
        # Build execution feedback if available
        feedback = ""
        if execution_result:
            if execution_result.get('success'):
                feedback = "Previous code passed all tests."
            else:
                error_msg = execution_result.get('message', '')
                tests_passed = execution_result.get('tests_passed', 0)
                total_tests = execution_result.get('total_tests', 3)
                feedback = f"Previous code failed ({tests_passed}/{total_tests} tests passed): {error_msg}"
        
        # Build the prompt
        user_prompt = f"""Write the Python function `{function_name}` for this problem:

{problem}

Tests it must pass:
{chr(10).join(test_cases)}

{effort_instruction}

{feedback}

Output ONLY the Python code starting with 'def {function_name}'. Nothing else."""

        # Call LLM with validation and retry
        max_retries = 4
        for attempt in range(max_retries):
            response = call_llm_openrouter(
                user_prompt=user_prompt,
                system_prompt=self.system_prompt,
                model=self.model_name,
                max_tokens=500,
                temperature=temperature  # Dynamic temperature based on turn
            )
            
            if not response:
                print(f"    ⚠️  Empty response, retrying... (attempt {attempt + 1})")
                continue
            
            # Extract only the code
            code = extract_code_only(response)
            
            if not code:
                print(f"    ⚠️  No code extracted, retrying... (attempt {attempt + 1})")
                continue
            
            # Validate output
            if is_valid_code(code, function_name):
                return code
            else:
                print(f"    ⚠️  Invalid code output, retrying... (attempt {attempt + 1})")
                continue
        
        # Last resort: return a basic template if all retries fail
        fallback = f"""def {function_name}(*args, **kwargs):
    # TODO: Implement solution
    pass"""
        print(f"    ⚠️  All retries failed, using fallback code")
        
        return fallback
