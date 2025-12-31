#!/usr/bin/env python3
"""
Test script for the multi-turn conversation generation
"""

from create_dataset import generate_conversation

def test_simple_conversation():
    """Test a simple conversation generation"""
    
    # Simple test problem
    problem_text = "Write a function that returns the sum of two numbers"
    test_cases = [
        "assert sum_numbers(2, 3) == 5",
        "assert sum_numbers(0, 0) == 0",
        "assert sum_numbers(-1, 1) == 0"
    ]
    
    # Simple student system prompt
    student_system_prompt = """You are a student learning Python programming. You ask questions and need help with coding problems. Be curious and ask follow-up questions."""
    
    print("Testing conversation generation...")
    print(f"Problem: {problem_text}")
    print("=" * 50)
    
    try:
        conversation = generate_conversation(
            problem_text=problem_text,
            test_cases=test_cases,
            max_turns=4,
            student_system_prompt=student_system_prompt
        )
        
        print("Generated conversation:")
        for turn in conversation:
            print(f"\nTurn {turn['turn']} - {turn['role'].upper()}:")
            print(turn['content'])
            if 'execution_result' in turn:
                print(f"\nExecution result: {turn['execution_result']}")
            print("-" * 30)
            
        return True
        
    except Exception as e:
        print(f"Error during conversation generation: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_conversation()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")