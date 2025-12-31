from openai import OpenAI
import json
import os
from datetime import datetime
import uuid
from llm_calling import call_llm_local, call_llm_openrouter
import prompts.instructor_prompts.instructor_prompt as instructor_prompt
from run_python import run_python_code
import re

def extract_func_name_from_tests(test_cases):
    for case in test_cases:
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', case)
        if match:
            return match.group(1)
    return None




def generate_conversation(problem_text, test_cases, max_turns, student_system_prompt):
    """Generate a multi-turn conversation between student and helper"""
    conversation = []
    error_context = None 
    
    with open('prompts/student_prompts/personality/prompts_v2/instructor_prompt.txt', 'r') as f:
        instructor_system_prompt = f.read()
    
    student_user_prompt = "Ask any question related to the problem: " + problem_text + ". Your conversation will be quoted as a student speaking in a professional tone. You are conversing as the student"
    
    fn_name = extract_func_name_from_tests(test_cases)
    print(fn_name)
    function_name_note = f"\Write a function named: {fn_name}" if fn_name else ""

    seeded_student = (
        "<student>" + "Hi! I'm working on this problem: " + problem_text +
        "\nI'm not sure how to get started. Could you work on this problem." + function_name_note +
        "</student>"
    )

    conversation.append({
        "role": "student",
        "content": seeded_student,
        "turn": 1
    })
    
    starting_turn = 2
    student_response = seeded_student

    for turn in range(starting_turn, starting_turn + max_turns):
        print(f"Turn {turn}")
        if turn % 2 == 1:
            print("Student turn") 
            student_user_prompt_with_error = student_user_prompt

            if error_context:
                error_prompt = f"NOTE: The previous code attempt failed with the following error:\n{error_context['message']}"
                student_user_prompt_with_error += error_prompt
                
            student_user_prompt_with_error += "\nThe conversation so far is: " + conv_history

            student_response = call_llm_openrouter(student_user_prompt_with_error, student_system_prompt,model="qwen/qwen3-235b-a22b-2507")
            if not student_response or not student_response.strip():
                student_response = call_llm_openrouter(student_user_prompt_with_error, student_system_prompt,model="qwen/qwen3-235b-a22b-2507")

            conversation.append({
                "role": "student",
                "content": student_response, 
                "turn": turn
            })
            
        else:
            print("Helper turn")
            instructor_user_prompt = "As a python generator, just give the python code to:" + student_response 

            conv_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])
            conv_history_note = "\nThe conversation so far is:\n" + conv_history if conv_history else ""
            
            helper_prompt = (
                instructor_user_prompt +
                conv_history_note +
                "\n\nYou must respond with Python code only, wrapped in <python>...</python> tags. "
                "Do not include any explanation outside the tags."
            )
            
            helper_response = call_llm_openrouter(helper_prompt, instructor_system_prompt,model="qwen/qwen3-235b-a22b-thinking-2507")
            
            execution_result = run_python_code(helper_response, test_cases)
            
            if not execution_result['success']:
                error_context = execution_result
            else:
                error_context = None  

            conversation.append({
                "role": "helper",
                "content": helper_response,
                "execution_result": execution_result['success'] if execution_result['success'] else False,
                "turn": turn 
            })
            
            if execution_result['success']:
                break
    
    return conversation

def process_mbpp_conversations():
    """Process MBPP dataset and generate conversations"""

    with open('benchmarks/mbpp.jsonl', 'r') as f:
        problems = [json.loads(line) for line in f]

    # Dictionary to map personality keys to file paths
    personality_paths = {
        'CONFUSED_STUDENT': 'prompts/student_prompts/personality/prompts_v2/confused_student.txt',
        'IMPATIENT_STUDENT': 'prompts/student_prompts/personality/prompts_v2/impatient_student.txt',
        # 'OVERCONFIDENT_WRONG': 'prompts/student_prompts/personality/prompts_v2/overconfident_wrong.txt',
        # 'SYNTAX_STRUGGLER': 'prompts/student_prompts/personality/prompts_v2/syntax_struggler.txt',
        # 'PROGRAMMING_HELPER': 'prompts/student_prompts/personality/prompts_v2/programming_helper.txt'
    }

    for selected_personality in personality_paths.keys():

        with open(personality_paths[selected_personality], 'r') as f:
            student_system_prompt = f.read()
            
        for i, problem in enumerate(problems[5:7]):
            print(f"Processing problem {i+1}: {problem['text'][:50]}...")
            
            conversation = generate_conversation(problem['text'],problem['test_list'],7,student_system_prompt)
            
            record = {
                "id": str(uuid.uuid4()),
                "task_id": problem['task_id'],
                "personality": selected_personality,
                "problem_text": problem['text'],
                "test_cases": problem['test_list'],
                "conversation": conversation,
                "timestamp": datetime.now().isoformat()
            }
            
            filename = f'data/06_11_2025/{selected_personality.lower()}_conversations.json'
            if not os.path.exists(filename):
                with open(filename, 'w') as f:
                    f.write('[\n')
            
            with open(filename, 'a') as f:
                json.dump(record, f)
                f.write(',\n')


process_mbpp_conversations()
