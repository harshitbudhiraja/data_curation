"""Migration script to add quality_bucket column to existing database."""
import sqlite3
from pathlib import Path

# Database path
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "backend" / "conversations.db"

def migrate_add_quality_bucket():
    """Add quality_bucket column to conversations table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(conversations)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'quality_bucket' not in columns:
        print("Adding quality_bucket column...")
        cursor.execute("ALTER TABLE conversations ADD COLUMN quality_bucket VARCHAR")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_conversations_quality_bucket ON conversations (quality_bucket)")
        conn.commit()
        print("✅ Successfully added quality_bucket column")
    else:
        print("✅ quality_bucket column already exists")
    
    conn.close()

if __name__ == "__main__":
    migrate_add_quality_bucket()
