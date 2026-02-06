"""Import strategy1_05_02_2026-2 data into database."""
import json
import sqlite3
from pathlib import Path

# Database path
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "backend" / "conversations.db"
DATA_DIR = BASE_DIR / "data" / "strategy1_05_02_2026-2"

def import_strategy_data():
    """Import conversations from strategy1_05_02_2026-2 folder."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    imported_count = 0
    
    print(f"Importing from {DATA_DIR.name}...")
    
    # Find all conversation JSON files
    for json_file in DATA_DIR.glob("*_conversations.json"):
        try:
            with open(json_file, 'r') as f:
                conversations = json.load(f)
            
            for conv in conversations:
                # Check if already exists
                cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv['id'],))
                if cursor.fetchone():
                    continue
                
                # Insert new conversation
                cursor.execute("""
                    INSERT INTO conversations (
                        id, task_id, personality, problem_text, test_cases, 
                        conversation, execution_result, solved, tests_passed, 
                        total_tests, turns, timestamp, date_folder, discarded, quality_bucket
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conv['id'],
                    conv['task_id'],
                    conv['personality'],
                    conv['problem_text'],
                    json.dumps(conv['test_cases']),
                    json.dumps(conv['conversation']),
                    json.dumps(conv.get('execution_result')),
                    conv.get('solved', False),
                    conv.get('tests_passed', 0),
                    conv.get('total_tests', 0),
                    conv.get('turns', 0),
                    conv.get('timestamp', ''),
                    DATA_DIR.name,
                    False,
                    conv.get('quality_bucket')
                ))
                imported_count += 1
            
            conn.commit()
            print(f"  ✅ Imported {json_file.name}")
            
        except Exception as e:
            print(f"  ❌ Error importing {json_file.name}: {e}")
            conn.rollback()
    
    conn.close()
    print(f"\n🎉 Imported {imported_count} conversations")

if __name__ == "__main__":
    import_strategy_data()
