import json
import time
import re
from llm_calling import call_llm_openrouter
from run_python import run_python_code


def extract_func_name_from_tests(test_cases):
    forp case in test_cases:
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', case)
        if match:
            return match.group(1)
    return None

def load_mbpp_questions(file_path='benchmarks/mbpp.jsonl'):
    questions = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            questions.append(json.loads(line))
    return questions

def strip_python_tags(text):
    """Extract code from <python></python> tags, if present."""
    import re
    match = re.search(r"<python>(.*?)</python>", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def classify_questions():
    print("Classifying questions...")
    mbpp_questions = load_mbpp_questions()
    results = {"easy": [], "medium": [], "difficult": []}
    system_prompt = """
    You are a Python code generator. Generate clean, executable Python code based on user requirements.

    Requirements:
    - Code must be complete and ready to run
    - Include all necessary imports
    - Use clear variable names and handle common errors
    - Add brief comments for complex logic

    Do not include any explanations outside the code block.
    """    
    for q in mbpp_questions:
        print(f"Classifying question: {q['task_id']}")
        user_prompt = q["text"]
        trial = 0
        solved = False
        code = ""
        error_messages = []
        function_name = extract_func_name_from_tests(q["test_list"])
        while trial < 1 and not solved:

            if trial == 0:
                llm_input = f"Write a Python function to solve the following: {user_prompt}. Wrap your solution in <python> </python> tags. Write a function named: {function_name}"
            else:
                print("error_messages:", error_messages)
                llm_input = (
                    f"The previous code failed with this error:\n{error_messages[-1] if error_messages else ''}\n"
                    f"Please rewrite the code to solve: {user_prompt}. Wrap your solution in <python> </python> tags."
                )
            llm_response = call_llm_openrouter(system_prompt,llm_input,model="qwen/qwen3-coder-30b-a3b-instruct")
            # code = strip_python_tags(llm_response)
            code = llm_response
            run_result = run_python_code(llm_response,q["test_list"])

            q["code"] = llm_response
            q["run_result"] = run_result
            # print(run_result)
            if run_result["success"]:
                solved = True
                q["trial"] = trial
                if trial == 0:
                    results["easy"].append(q)
                elif trial == 1 or trial == 2:
                    results["medium"].append(q)
                break
            else:
                error_messages.append(run_result.get("error", "Unknown error"))
                trial += 1

        if not solved:
            q["trial"] = trial
            results["difficult"].append(q)

    def simplify(qs): return [{"task_id": q["task_id"], "text": q["text"], "code": q["code"], "run_result": q["run_result"], 'trial': q['trial']} for q in qs]

    summary = {
        "easy": simplify(results["easy"]),
        "medium": simplify(results["medium"]),
        "difficult": simplify(results["difficult"])
    }

    with open("mbpp_question_difficulty_classification.json", "w", encoding="utf-8") as out_f:
        json.dump(summary, out_f, indent=2, ensure_ascii=False)

    print("Classification complete. Results written to mbpp_question_difficulty_classification.json.")
    print({k: len(v) for k,v in summary.items()})

if __name__ == "__main__":
    print("Starting classification...")
    classify_questions()
