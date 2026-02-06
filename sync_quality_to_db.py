"""Sync quality_bucket data from JSON files to database."""
import json
import sqlite3
from pathlib import Path

# Database path
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "backend" / "conversations.db"
DATA_DIR = BASE_DIR / "data"

def sync_quality_to_db():
    """Update database with quality_bucket from JSON files."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    updated_count = 0
    
    # Iterate through date folders
    for date_folder in DATA_DIR.iterdir():
        if not date_folder.is_dir() or date_folder.name.startswith('.'):
            continue
        
        print(f"Processing {date_folder.name}...")
        
        # Find all conversation JSON files
        for json_file in date_folder.glob("*_conversations.json"):
            try:
                with open(json_file, 'r') as f:
                    conversations = json.load(f)
                
                for conv in conversations:
                    conv_id = conv['id']
                    quality_bucket = conv.get('quality_bucket')
                    
                    if quality_bucket:
                        # Update the database
                        cursor.execute(
                            "UPDATE conversations SET quality_bucket = ? WHERE id = ?",
                            (quality_bucket, conv_id)
                        )
                        if cursor.rowcount > 0:
                            updated_count += 1
                
                conn.commit()
                print(f"  ✅ Processed {json_file.name}")
                
            except Exception as e:
                print(f"  ❌ Error processing {json_file.name}: {e}")
    
    conn.close()
    print(f"\n🎉 Updated {updated_count} conversations with quality buckets")

if __name__ == "__main__":
    sync_quality_to_db()
