"""Tutor agent implementation adapted for data_curation."""
import sys
import os
import re
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_calling import call_llm_openrouter
from langchain_core.messages import SystemMessage


def inject_bug(code: str, bug_type: str) -> str:
    """Programmatically inject a bug into working code.
    
    Args:
        code: Working Python code
        bug_type: Type of bug to inject ('syntax' or 'logic')
    
    Returns:
        Code with injected bug
    """
    lines = code.split('\n')
    
    if bug_type == 'syntax':
        # 10 different syntax bug types - pick one randomly
        syntax_bugs = []
        
        # Bug 1: Remove colon from function definition
        for i, line in enumerate(lines):
            if 'def ' in line and ':' in line:
                syntax_bugs.append(('remove_colon', i, lambda l: l.replace(':', '', 1)))
        
        # Bug 2: Remove closing parenthesis from function parameters
        for i, line in enumerate(lines):
            if 'def ' in line and ')' in line:
                syntax_bugs.append(('missing_paren_def', i, lambda l: l[:l.rfind(')')] + l[l.rfind(')')+1:]))
        
        # Bug 3: Remove closing parenthesis from return statement
        for i, line in enumerate(lines):
            if 'return' in line and ')' in line:
                syntax_bugs.append(('missing_paren_return', i, lambda l: l[:l.rfind(')')] + l[l.rfind(')')+1:]))
        
        # Bug 4: Remove opening parenthesis
        for i, line in enumerate(lines):
            if 'return' in line and '(' in line:
                syntax_bugs.append(('missing_open_paren', i, lambda l: l.replace('(', '', 1)))
        
        # Bug 5: Add extra comma in function parameters
        for i, line in enumerate(lines):
            if 'def ' in line and ',' in line:
                syntax_bugs.append(('extra_comma', i, lambda l: l.replace(',', ',,', 1)))
        
        # Bug 6: Missing equals in assignment (if any)
        for i, line in enumerate(lines):
            if '=' in line and 'return' not in line and 'def' not in line:
                syntax_bugs.append(('missing_equals', i, lambda l: l.replace('=', '', 1)))
        
        # Bug 7: Typo in keyword (def -> deff)
        for i, line in enumerate(lines):
            if 'def ' in line:
                syntax_bugs.append(('typo_def', i, lambda l: l.replace('def ', 'deff ', 1)))
        
        # Bug 8: Typo in return keyword
        for i, line in enumerate(lines):
            if 'return' in line:
                syntax_bugs.append(('typo_return', i, lambda l: l.replace('return', 'retrun', 1)))
        
        # Bug 9: Missing closing bracket
        for i, line in enumerate(lines):
            if ']' in line:
                syntax_bugs.append(('missing_bracket', i, lambda l: l[:l.rfind(']')] + l[l.rfind(']')+1:]))
        
        # Bug 10: Wrong indentation (dedent a line that should be indented)
        for i, line in enumerate(lines):
            if i > 0 and line.startswith('    ') and 'return' in line:
                syntax_bugs.append(('wrong_indent', i, lambda l: l.lstrip()))
        
        if syntax_bugs:
            bug_name, line_idx, transform = random.choice(syntax_bugs)
            original = lines[line_idx]
            lines[line_idx] = transform(original)
            print(f"    🐛 Syntax bug '{bug_name}' on line {line_idx+1}: {original.strip()[:50]}")
            return '\n'.join(lines)
    
    elif bug_type == 'logic':
        # 10 different logic bug types - pick one randomly
        logic_bugs = []
        
        # Bug 1: Change set intersection to union (& to |)
        for i, line in enumerate(lines):
            if '&' in line and 'set(' in line:
                logic_bugs.append(('intersection_to_union', i, lambda l: l.replace('&', '|', 1)))
        
        # Bug 2: Change set union to intersection (| to &)
        for i, line in enumerate(lines):
            if '|' in line and 'set(' in line:
                logic_bugs.append(('union_to_intersection', i, lambda l: l.replace('|', '&', 1)))
        
        # Bug 3: Remove one set() call (causes type error)
        for i, line in enumerate(lines):
            if line.count('set(') >= 2:
                logic_bugs.append(('remove_set', i, lambda l: l.replace('set(', '(', 1)))
        
        # Bug 4: Remove tuple() wrapper (wrong return type)
        for i, line in enumerate(lines):
            if 'tuple(' in line and 'return' in line:
                logic_bugs.append(('remove_tuple', i, lambda l: l.replace('tuple(', '(')))
        
        # Bug 5: Change list() to tuple() or vice versa
        for i, line in enumerate(lines):
            if 'list(' in line:
                logic_bugs.append(('list_to_tuple', i, lambda l: l.replace('list(', 'tuple(')))
            if 'tuple(' in line:
                logic_bugs.append(('tuple_to_list', i, lambda l: l.replace('tuple(', 'list(')))
        
        # Bug 6: Remove sorted() call (causes order issues)
        for i, line in enumerate(lines):
            if 'sorted(' in line:
                logic_bugs.append(('remove_sorted', i, lambda l: l.replace('sorted(', '(')))
        
        # Bug 7: Change comparison operator (== to !=, < to >, etc.)
        for i, line in enumerate(lines):
            if ' == ' in line:
                logic_bugs.append(('flip_equals', i, lambda l: l.replace(' == ', ' != ', 1)))
            if ' < ' in line:
                logic_bugs.append(('flip_less', i, lambda l: l.replace(' < ', ' > ', 1)))
            if ' > ' in line:
                logic_bugs.append(('flip_greater', i, lambda l: l.replace(' > ', ' < ', 1)))
        
        # Bug 8: Change 'in' to 'not in'
        for i, line in enumerate(lines):
            if ' in ' in line and 'not in' not in line:
                logic_bugs.append(('in_to_not_in', i, lambda l: l.replace(' in ', ' not in ', 1)))
        
        # Bug 9: Off-by-one in range (if present)
        for i, line in enumerate(lines):
            if 'range(' in line:
                logic_bugs.append(('off_by_one', i, lambda l: l.replace('range(', 'range(1, ') if 'range(1' not in l else l))
        
        # Bug 10: Wrong variable name in operation
        for i, line in enumerate(lines):
            if 'tuple1' in line and 'tuple2' in line:
                logic_bugs.append(('wrong_var', i, lambda l: l.replace('tuple2', 'tuple1', 1)))
        
        if logic_bugs:
            bug_name, line_idx, transform = random.choice(logic_bugs)
            original = lines[line_idx]
            lines[line_idx] = transform(original)
            print(f"    🐛 Logic bug '{bug_name}' on line {line_idx+1}: {original.strip()[:50]}")
            return '\n'.join(lines)
    
    print(f"    ⚠️  No suitable location found for {bug_type} bug injection")
    return code


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
            turn_count: Current turn number (to adjust helpfulness)
            execution_result: Previous execution result if any
        
        Returns:
            Tutor's response as Python code
        """
        # ENFORCE MINIMUM 4 TURNS: Determine if we should inject bugs
        should_inject_bug = False
        bug_type = None
        
        if turn_count <= 2:
            # First response MUST have a syntax bug
            should_inject_bug = True
            bug_type = 'syntax'
            instruction = "Write CORRECT Python code that solves the problem."
        elif turn_count <= 4:
            # Second/third response - inject logic bug
            should_inject_bug = True
            bug_type = 'logic'
            instruction = "Write CORRECT Python code that solves the problem."
        else:
            # After turn 4, allow correct code
            should_inject_bug = False
            instruction = "Write CORRECT code that passes all tests."
        
        # Build execution feedback if available
        feedback = ""
        if execution_result:
            if execution_result.get('success'):
                feedback = "Previous code passed all tests."
            else:
                error_msg = execution_result.get('message', '')
                feedback = f"Previous code failed: {error_msg}"
        
        # Ask LLM for CORRECT code (we'll inject bugs ourselves)
        user_prompt = f"""Write the Python function `{function_name}` for this problem:

{problem}

Tests it must pass:
{chr(10).join(test_cases)}

{instruction}

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
                temperature=0.3
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
                # INJECT BUG if needed
                if should_inject_bug:
                    original_code = code
                    code = inject_bug(code, bug_type)
                    if code != original_code:
                        print(f"    🐛 Injected {bug_type} bug into code")
                    else:
                        print(f"    ⚠️  Bug injection failed - no suitable location found")
                
                return code
            else:
                print(f"    ⚠️  Invalid code output, retrying... (attempt {attempt + 1})")
                continue
        
        # Last resort: return a basic template if all retries fail
        fallback = f"""def {function_name}(tuple1, tuple2):
    result = []
    for item in tuple1:
        if item in tuple2:
            result.append(item)
    return tuple(result)"""
        print(f"    ⚠️  All retries failed, using fallback code")
        
        # Inject bug into fallback too if needed
        if should_inject_bug:
            fallback = inject_bug(fallback, bug_type)
        
        return fallback
