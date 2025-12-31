import json
import ast

# Utility to find the first function name in a code block
def extract_first_function_name(code_str):
    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except Exception:
        pass
    return None

# Load the conversations file
convs_path = "data/05_11_2025/mbpp/confused_student_conversations.json"
with open(convs_path, "r") as f:
    data_str = f.read().rstrip()
    if data_str.endswith(",\n"):
        data_str = data_str[:-2] + "\n]"
    conversations = json.loads(data_str)

# Load MBPP test cases only once for efficiency
mbpp_tests_by_taskid = {}
try:
    with open("benchmarks/mbpp.jsonl", "r") as mf:
        for line in mf:
            j = json.loads(line)
            bid = str(j.get("task_id"))
            mbpp_tests_by_taskid[bid] = j.get("test_list", [])
except Exception:
    pass

for conv_obj in conversations:
    task_id = conv_obj.get("task_id")
    problem = conv_obj.get("problem_text")
    conv_list = conv_obj.get("conversation", [])

    test_cases = mbpp_tests_by_taskid.get(str(task_id), [])

    for msg in conv_list:
        if msg.get("role") == "helper" and "<python>" in msg.get("content", ""):
            print(f"\nTask ID: {task_id}")
            print(f"Problem: {problem}")
            print("Code extracted from helper:")
            print(msg["content"])

            if not test_cases:
                print("No test cases found for this problem. Skipping code execution.")
                continue

            # Extract code block between <python> ... </python>, else just use content
            content = msg.get("content", "")
            if "<python>" in content and "</python>" in content:
                code = content.split("<python>", 1)[1].split("</python>", 1)[0].strip()
            else:
                code = content

            fn_name = extract_first_function_name(code)
            if not fn_name:
                print("No function found in code. Skipping assertions.")
                print("-" * 60)
                continue

            # Prepare code for exec, ensure function is defined and assertions can run
            exec_code = code + "\n"
            # Compose assertions directly from mbpp.jsonl for this task (they use the correct function name)
            for assertion in test_cases:
                exec_code += f"\n{assertion}"

            # Run code and catch assertion (or any) errors
            print("Running MBPP test assertions:")
            try:
                local_ns = {}
                exec(exec_code, {}, local_ns)
                print("All assertions passed!")
            except AssertionError:
                print("FAILED: One or more assertions failed.")
            except Exception as exc:
                print(f"ERROR while running assertions: {exc}")
            print("-" * 60)
