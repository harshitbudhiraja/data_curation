"""Dataset generation using autonomous LangChain agents."""
import json
import os
import uuid
import re
from datetime import datetime
from multiprocessing import Process
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from simulation.graph import create_simulation_graph, AgentState

# Load environment variables from .env file
load_dotenv()


def sanitize_problem_data(problem):
    """Rename functions starting with 'test_' to 'check_' to avoid pytest naming conflicts.
    
    Args:
        problem: MBPP problem dict with 'text' and 'test_list' fields
    
    Returns:
        Sanitized problem dict
    """
    # Extract function name from test cases
    test_cases = problem.get('test_list', [])
    if not test_cases:
        return problem
    
    # Look for test_ prefix in function names
    match = re.search(r'assert\s+(test_\w+)\(', str(test_cases))
    if not match:
        return problem  # No test_ prefix found, return as-is
    
    bad_name = match.group(1)  # e.g., "test_duplicate"
    good_name = bad_name.replace("test_", "check_", 1)  # e.g., "check_duplicate"
    
    print(f"  🔧 Sanitizing: {bad_name} → {good_name}")
    
    # Fix test cases
    new_test_list = []
    for test in test_cases:
        new_test_list.append(test.replace(f"{bad_name}(", f"{good_name}("))
    problem['test_list'] = new_test_list
    
    # Fix problem text
    problem['text'] = problem['text'].replace(bad_name, good_name)
    
    # Fix code if present
    if 'code' in problem:
        problem['code'] = problem['code'].replace(f"def {bad_name}(", f"def {good_name}(")
    
    return problem


def extract_func_name_from_tests(test_cases):
    """Extract function name from test cases."""
    for case in test_cases:
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', case)
        if match:
            return match.group(1)
    return None


def process_personality(selected_personality, prompt_path, problems, output_dir, start_idx=1, end_idx=201):
    """Process one personality - designed to run in parallel.
    
    Args:
        start_idx: Starting problem index (1-based, inclusive)
        end_idx: Ending problem index (1-based, exclusive)
    """
    print(f"\n🚀 Generating conversations for: {selected_personality} (problems {start_idx}-{end_idx-1})")
    
    # Load personality prompt
    with open(prompt_path, 'r') as f:
        personality_prompt = f.read()
    
    # Check if file exists and load existing conversations
    filename = f'{output_dir}/{selected_personality.lower()}_conversations.json'
    conversations = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            conversations = json.load(f)
        print(f"  📂 [{selected_personality}] Loaded {len(conversations)} existing conversations")
    
    # Process problems in range
    for i, problem in enumerate(problems[start_idx:end_idx]):
        actual_idx = start_idx + i
        print(f"  [{selected_personality}] Processing problem {actual_idx}/{end_idx-1}: {problem['text'][:50]}...")
        
        try:
            # Create graph for this conversation
            app = create_simulation_graph()
            
            # Initial state
            initial_state = {
                "messages": [],
                "problem_text": problem['text'],
                "test_cases": problem['test_list'][:3],  # Use all 3 test cases
                "personality_prompt": personality_prompt,
                "personality": selected_personality,
                "turn_count": 0,
                "max_turns": 10,  # Maximum conversation turns
                "execution_result": None,
                "solved": False,
                "execution_history": []
            }
            
            # Run the agent conversation with increased recursion limit
            final_state = app.invoke(
                initial_state,
                config={"recursion_limit": 100}
            )
            
            # Format conversation for storage with execution results
            formatted_conversation = []
            execution_history = final_state.get('execution_history', [])
            
            for msg in final_state['messages']:
                msg_dict = {
                    "role": msg.name if hasattr(msg, 'name') else msg.get('role', 'unknown'),
                    "content": msg.content if hasattr(msg, 'content') else msg.get('content', ''),
                    "turn": len(formatted_conversation) + 1
                }
                
                # If this is a tutor message, attach the execution result for this turn
                if msg_dict["role"] == "tutor":
                    # Find execution result for this turn
                    for exec_result in execution_history:
                        if exec_result["turn"] == msg_dict["turn"]:
                            msg_dict["execution"] = exec_result
                            break
                
                formatted_conversation.append(msg_dict)
            
            # Create record
            record = {
                "id": str(uuid.uuid4()),
                "task_id": problem['task_id'],
                "personality": selected_personality,
                "problem_text": problem['text'],
                "test_cases": problem['test_list'],
                "conversation": formatted_conversation,
                "execution_result": final_state.get('execution_result'),
                "solved": final_state.get('solved', False),
                "tests_passed": final_state.get('execution_result', {}).get('tests_passed', 0) if final_state.get('execution_result') else 0,
                "total_tests": len(problem['test_list'][:3]),
                "turns": final_state['turn_count'],
                "timestamp": datetime.now().isoformat()
            }
            
            conversations.append(record)
            
            # Print summary with test progress
            tests_passed = record['tests_passed']
            total_tests = record['total_tests']
            print(f"    ✅ [{selected_personality}] Completed: {final_state['turn_count']} turns, Solved: {final_state.get('solved', False)}, Tests: {tests_passed}/{total_tests}")
            
            # Save after each problem (incremental save to prevent data loss)
            filename = f'{output_dir}/{selected_personality.lower()}_conversations.json'
            with open(filename, 'w') as f:
                json.dump(conversations, f, indent=2)
            
        except Exception as e:
            print(f"    ❌ [{selected_personality}] Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Final save (already saved incrementally, but do one more for safety)
    filename = f'{output_dir}/{selected_personality.lower()}_conversations.json'
    with open(filename, 'w') as f:
        json.dump(conversations, f, indent=2)
    print(f"✅ [{selected_personality}] Saved {len(conversations)} conversations to {filename}")


def process_mbpp_conversations(start_problem=1, end_problem=201):
    """Process MBPP dataset and generate conversations using agents.
    
    Args:
        start_problem: Starting problem number (1-based, inclusive)
        end_problem: Ending problem number (1-based, exclusive)
    """
    
    # Load MBPP problems
    with open('benchmarks/mbpp.jsonl', 'r') as f:
        problems = [json.loads(line) for line in f]
    
    # Sanitize problems to avoid pytest naming conflicts
    print("🔍 Checking for test_ naming conflicts...")
    problems = [sanitize_problem_data(p) for p in problems]
    
    # Create dated output folder with auto-increment
    today = datetime.now().strftime("%d_%m_%Y")
    output_dir = f'data/{today}'
    
    # If folder exists, append -1, -2, etc.
    if os.path.exists(output_dir):
        counter = 1
        while os.path.exists(f'data/{today}-{counter}'):
            counter += 1
        output_dir = f'data/{today}-{counter}'
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Personality prompts (all in prompts/ folder)
    personality_paths = {
        'CONFUSED_STUDENT': 'prompts/confused_student.txt',
        'IMPATIENT_STUDENT': 'prompts/impatient_student.txt',
        'OVERCONFIDENT_WRONG': 'prompts/overconfident_wrong.txt',
        'SYNTAX_STRUGGLER': 'prompts/syntax_struggler.txt',
        'PROGRAMMING_HELPER': 'prompts/programming_helper.txt'
    }
    
    print(f"\n🎯 Starting parallel generation for problems {start_problem}-{end_problem-1} across 5 personalities...")
    print(f"💾 Output directory: {output_dir}/")
    
    # Create processes for each personality
    processes = []
    for personality, prompt_path in personality_paths.items():
        p = Process(target=process_personality, args=(personality, prompt_path, problems, output_dir, start_problem, end_problem))
        processes.append(p)
        p.start()
    
    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    print("\n🎉 Dataset generation complete!")


if __name__ == "__main__":
    import sys
    
    # Allow command line arguments: python create_dataset.py [start] [end]
    # Example: python create_dataset.py 1 201  (problems 1-200)
    # Example: python create_dataset.py 155 201  (resume from 155-200)
    
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 101
    
    print(f"🎬 Starting dataset generation: problems {start} to {end-1}")
    process_mbpp_conversations(start_problem=start, end_problem=end)





