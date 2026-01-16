import json
import os
import re
import glob
import uuid

# --- CONFIGURATION ---
# 1. Matches your actual data folder
INPUT_DIR = "data/16_01_2026-2"   

# 2. Creates a new, safe output folder
OUTPUT_DIR = "data/golden_3"         

def clean_text(text):
    """Removes LLM artifacts, tokenizer leaks, and style instructions."""
    if not text: return ""
    
    # Remove specific tokenizer tags
    text = re.sub(r'<\|[^|]+\|>', '', text)
    
    # Remove style instructions leaking into output (e.g., "Tone: Confused")
    text = re.sub(r'Tone:.*?Action:', '', text, flags=re.IGNORECASE)
    
    # Remove "thought" chains if present
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    return text.strip()

def process_conversations():
    print(f"🚀 Starting Golden Dataset V3 Generation...")
    print(f"📂 Input:  {INPUT_DIR}")
    print(f"📂 Output: {OUTPUT_DIR}\n")

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Error: Input directory '{INPUT_DIR}' does not exist.")
        return

    # Find all .json files
    files = glob.glob(os.path.join(INPUT_DIR, "*.json"))
    
    if not files:
        print(f"❌ No .json files found in {INPUT_DIR}")
        return

    # Process each file individually
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"  Processing {filename}...")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        clean_data_for_file = []
        rescued_count = 0
        total_discarded = 0
        
        for entry in data:
            # --- STEP 1: RESCUE FALSE FAILURES ---
            # Trust the actual test results over the 'solved' flag
            total_tests = entry.get('total_tests', 0)
            tests_passed = entry.get('tests_passed', 0)
            
            if total_tests > 0 and tests_passed == total_tests:
                if not entry.get('solved', False):
                    entry['solved'] = True
                    rescued_count += 1
            
            # --- STEP 2: STRICT FILTERING ---
            
            # Filter A: Must be Solved
            if not entry.get('solved', False):
                total_discarded += 1
                continue

            # Filter B: Skip "Inception" Hallucinations
            # (If the Tutor started roleplaying as the Student in the code block)
            has_hallucination = False
            for turn in entry['conversation']:
                if turn['role'] == 'tutor':
                    if "Student:" in turn['content'] or "Tutor:" in turn['content']:
                        has_hallucination = True
                        break
            if has_hallucination:
                total_discarded += 1
                continue

            # --- STEP 3: CLEANING & FORMATTING ---
            clean_msgs = []
            for turn in entry['conversation']:
                clean_msg = {
                    "role": turn['role'],
                    "content": clean_text(turn['content']),
                    "turn": turn.get('turn')
                }
                # Preserve execution results if present (for tutor messages)
                if 'execution' in turn:
                    clean_msg['execution'] = turn['execution']
                clean_msgs.append(clean_msg)
            
            # Keep original structure + New ID
            final_entry = entry.copy()
            final_entry['id'] = str(uuid.uuid4()) 
            final_entry['conversation'] = clean_msgs
            final_entry['dataset_version'] = "golden_3"
            
            clean_data_for_file.append(final_entry)

        # Write the cleaned list to the output folder (same filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, 'w') as out_f:
            json.dump(clean_data_for_file, out_f, indent=2)
            
        print(f"    ✅ Saved {len(clean_data_for_file)} conversations")
        print(f"    🚑 Rescued {rescued_count} false failures")
        print(f"    🗑️  Discarded {total_discarded} low-quality items")

    print(f"\n✅ DONE! Your separate JSON files are in: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_conversations()