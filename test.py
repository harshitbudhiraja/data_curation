from openai import OpenAI
import json
from datetime import datetime
import uuid


def process_batch(questions):
    results = []
    for i, question in enumerate(questions):
        answer = call_llm_local(question)
        
        record = {
            "id": str(uuid.uuid4()),
            "serial_number": i+1,
            "from": "user",
            "value": question,
            "type": "llm", 
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }
        
        results.append(record)
        
        # Write to JSONL file
        with open('llm_responses.jsonl', 'a') as f:
            json.dump(record, f)
            f.write('\n')
            
    return results

# Example usage
questions = [
    "Write a recursive Python function for Fibonacci numbers.",
    "Write a function to reverse a string in Python",
    "Write a function to check if a number is prime"
]

responses = process_batch(questions)
