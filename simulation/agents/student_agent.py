"""Student agent implementation adapted for data_curation."""
import sys
import os
import re
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_calling import call_llm_openrouter
from langchain_core.messages import HumanMessage, SystemMessage


def clean_response(response: str) -> str:
    """Clean student response of any unwanted tags/content."""
    if not response:
        return ""
    
    # Remove think tags (open or closed)
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<think>.*', '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove wrapper tags
    for tag in ['student', 'tutor', 'user', 'assistant', 'response']:
        response = re.sub(rf'<{tag}>\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(rf'\s*</{tag}>', '', response, flags=re.IGNORECASE)
    
    # Clean up whitespace
    response = response.strip()
    
    # Truncate if too long (student responses should be brief)
    lines = response.split('\n')
    if len(lines) > 10:
        response = '\n'.join(lines[:10])
    
    return response



class StudentAgent:
    """Student agent that asks questions and provides corrections."""
    
    def __init__(self, personality_prompt: str, personality_name: str = "CONFUSED_STUDENT", model_name: str = "openai/gpt-4o-mini"):
        self.model_name = model_name
        self.personality_prompt = personality_prompt
        self.personality_name = personality_name
        
        # Define styles per personality (using TONE instructions, not templates)
        self.styles = {
            "CONFUSED_STUDENT": {
                "opening": [
                    "Tone: Totally lost. Action: Admit you have no idea where to start with {problem_summary}.",
                    "Tone: Hesitant/Shy. Action: Ask for help with {problem_summary} but say you are confused.",
                    "Tone: Simple. Action: Ask for a very simple explanation of {problem_summary}."
                ],
                "feedback": [
                    "Tone: Confused. Action: Ask why you got the error {error_summary}. Act surprised.",
                    "Tone: Helpless. Action: Say you don't understand the error {error_summary} and need guidance.",
                    "Tone: Inquisitive. Action: Ask if the error {error_summary} is because of a specific line."
                ]
            },
            "IMPATIENT_STUDENT": {
                "opening": [
                    "Tone: Direct/Urgent. Action: Ask for the code for {problem_summary} immediately.",
                    "Tone: Annoyed. Action: Say you don't have time and just need the solution for {problem_summary}.",
                    "Tone: Concise. Action: Use as few words as possible to ask for {problem_summary}."
                ],
                "feedback": [
                    "Tone: Blunt. Action: State that it failed ({error_summary}) and tell the tutor to fix it.",
                    "Tone: Annoyed. Action: Complain that it's still not working (Error: {error_summary}).",
                    "Tone: Demanding. Action: Demand a fix for {error_summary} right now."
                ]
            },
            "OVERCONFIDENT_WRONG": {
                "opening": [
                    "Tone: Arrogant. Action: Claim {problem_summary} looks easy and ask for a quick confirmation.",
                    "Tone: Cocky. Action: Bet you can solve {problem_summary} faster, but ask for their take.",
                    "Tone: Skeptical. Action: Ask if they even know how to solve {problem_summary}."
                ],
                "feedback": [
                    "Tone: Dismissive. Action: Say the error {error_summary} must be a minor thing.",
                    "Tone: Corrective. Action: Incorrectly claim you know why {error_summary} happened.",
                    "Tone: Dubious. Action: Question if the test cases are even correct given {error_summary}."
                ]
            },
            "SYNTAX_STRUGGLER": {
                "opening": [
                    "Tone: Syntax-Confused. Action: Say you need help with {problem_summary} because Python syntax confuses you. MAX 10-25 words. Examples: 'help with this?? python syntax confuses me', 'can u help? im new to python syntax'",
                    "Tone: Syntax-Worried. Action: Complain about syntax errors with {problem_summary}. Keep it under 25 words.",
                    "Tone: Indentation-Focused. Action: Ask about {problem_summary} but mention indentation/syntax issues. Be brief (10-25 words)."
                ],
                "feedback": [
                    "Tone: Syntax-ONLY. Action: Ask ONLY about syntax for {error_summary} - colons, brackets, indentation, parentheses. MAX 10-25 words. Examples: 'is it a missing colon??', 'did u forget the bracket?', 'indentation error maybe?'. IGNORE logic completely!",
                    "Tone: Punctuation-Obsessed. Action: Focus ONLY on punctuation/syntax in {error_summary}. Ask about colons, brackets, semicolons. MAX 25 words. Don't mention logic or algorithms!",
                    "Tone: Syntax-Fixated. Action: Ask if {error_summary} is due to missing colon, bracket, or indentation. MAX 25 words. Sometimes suggest C/Java syntax by mistake (semicolons, for loops)."
                ]
            },
            "PROGRAMMING_HELPER": {
                "opening": [
                    "Tone: Expert/Direct. Action: Ask for help with {problem_summary} - be brief (10-15 words max). Examples: 'need help with minPath function - what's the best algo?', 'how should I approach the is_tree_balanced problem?'",
                    "Tone: Technical/Brief. Action: Ask about implementation for {problem_summary} - keep it under 15 words.",
                    "Tone: Professional/Concise. Action: Request algorithm approach for {problem_summary} - be direct and brief."
                ],
                "feedback": [
                    "Tone: Expert Fix Provider. Action: PROVIDE COMPLETE WORKING CODE FIX for {error_summary}. Don't just point out errors - GIVE THE EXACT CODE. Be technical and precise. Include the full corrected function or specific line changes.",
                    "Tone: Direct Code Fixer. Action: Identify the EXACT bug in {error_summary} and provide COMPLETE working code fix. No vague hints - show the actual code.",
                    "Tone: Aggressive Debugger. Action: Analyze {error_summary}, identify the bug, and provide COMPLETE code fix immediately. Be fast and technical."
                ]
            }
        }
    
    def generate_response(self, conversation_history: list, problem: str = None, function_name: str = None, execution_result: dict = None) -> str:
        """Generate student's response based on conversation history."""
        
        # Get styles for this personality (default to CONFUSED if not found)
        persona_styles = self.styles.get(self.personality_name, self.styles["CONFUSED_STUDENT"])
        
        # First turn - student starts the conversation
        if not conversation_history or len(conversation_history) == 0:
            opening_templates = persona_styles["opening"]
            style_instruction = random.choice(opening_templates).format(problem_summary=problem[:100].strip())
            
            user_prompt = f"""You are starting a conversation with a coding tutor.
You need help writing a Python function called `{function_name}`.

Problem: {problem}

Write an initial message asking for help.
Instructions:
{style_instruction}

Constraints:
- Be brief (1-2 sentences).
- Do NOT write the solution code yourself.
- Just ask for guidance or an initial implementation.
- Use natural language (typos represent the persona)."""
        
        else:
            # Get the last tutor message (the code they provided)
            last_tutor_msg = None
            for msg in reversed(conversation_history):
                role = msg.name if hasattr(msg, 'name') else msg.get('name', msg.get('role', ''))
                if role == 'tutor':
                    last_tutor_msg = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                    break
            
            # Build feedback about execution
            exec_feedback = ""
            if execution_result:
                if execution_result.get('success'):
                    exec_feedback = "The code passed all tests! Thank the tutor briefly and end the conversation."
                else:
                    tests_passed = execution_result.get('tests_passed', 0)
                    total_tests = execution_result.get('total_tests', 3)
                    error_msg = execution_result.get('message', 'tests failed')
                    exec_feedback = f"""The code FAILED ({tests_passed}/{total_tests} tests passed).
Error: {error_msg}

Point out what's wrong and suggest a fix. Be brief (2-3 sentences max).
DO NOT say it works or thank the tutor - the code is broken!
You can respond with just text, or text + a code snippet showing the fix."""
            
            # Styles for feedback/response
            error_hint = error_msg[:100] if 'error_msg' in locals() else "logic error"
            feedback_templates = persona_styles["feedback"]
            style_instruction = random.choice(feedback_templates).format(error_summary=error_hint)

            user_prompt = f"""The tutor gave you this code for the `{function_name}` function:

```python
{last_tutor_msg if last_tutor_msg else 'No code provided'}
```

{exec_feedback}

Remember: Stay focused on the `{function_name}` function.
Instructions:
{style_instruction}

CRITICAL CONSTRAINTS - FOLLOW EXACTLY:
- Follow your personality rules STRICTLY (check your system prompt)
- If you're PROGRAMMING_HELPER: Provide COMPLETE working code fixes, not explanations
- If you're SYNTAX_STRUGGLER: Ask ONLY about syntax (colons, brackets, indentation) - MAX 25 words
- If you're CONFUSED_STUDENT: Ask basic questions - MAX 15 words
- If you're IMPATIENT_STUDENT: Be demanding and brief - MAX 15 words
- If you're OVERCONFIDENT_WRONG: Be cocky and suggest fixes - MAX 25 words
- If the code works (all tests passed), just say "Works perfectly, thanks!" or similar.
- If the code FAILED, DO NOT say it works! Stay in character while pointing out the error."""
        
        # Call LLM
        max_retries = 3
        
        # Adjust max_tokens based on personality to enforce brevity
        if self.personality_name in ["CONFUSED_STUDENT", "IMPATIENT_STUDENT"]:
            max_tokens = 100  # Very short responses (5-15 words)
        elif self.personality_name in ["SYNTAX_STRUGGLER", "OVERCONFIDENT_WRONG"]:
            max_tokens = 150  # Short responses (10-25 words)
        elif self.personality_name == "PROGRAMMING_HELPER":
            max_tokens = 400  # Longer for code fixes, but still controlled
        else:
            max_tokens = 300  # Default
        
        for attempt in range(max_retries):
            response = call_llm_openrouter(
                user_prompt=user_prompt,
                system_prompt=self.personality_prompt,
                model=self.model_name,
                max_tokens=300,  # Keep student responses short
                temperature=0.5
            )
            
            if not response or not response.strip():
                print(f"    ⚠️  Student: Empty response, retrying... (attempt {attempt + 1})")
                continue
            
            # Clean the response
            response = clean_response(response)
            
            if not response:
                print(f"    ⚠️  Student: Response empty after cleaning, retrying... (attempt {attempt + 1})")
                continue
            
            return response
        
        # Fallback response
        if not conversation_history:
            return f"hey can you help me write the {function_name} function? not sure how to start"
        else:
            return "hmm that doesn't look right, can you check the logic again?"
