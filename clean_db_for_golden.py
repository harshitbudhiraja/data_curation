#!/usr/bin/env python3
"""Remove strategy1_10_02_2026-9 and strategy1_11_02_2026-Golden from database."""
import sys
sys.path.append('backend')
from database import SessionLocal, Conversation

db = SessionLocal()

print("=" * 80)
print("REMOVING OLD DATA FROM DATABASE")
print("=" * 80)

# Check what's in the database
folders = db.query(Conversation.date_folder).distinct().all()
print(f"\nCurrent folders in database:")
for folder in folders:
    count = db.query(Conversation).filter(Conversation.date_folder == folder[0]).count()
    print(f"  {folder[0]}: {count} conversations")

# Count conversations to delete
to_delete_1 = db.query(Conversation).filter(Conversation.date_folder == 'strategy1_10_02_2026-9').count()
to_delete_2 = db.query(Conversation).filter(Conversation.date_folder == 'strategy1_11_02_2026-Golden').count()

print(f"\n" + "=" * 80)
print("DELETING")
print("=" * 80)
print(f"\nstrategy1_10_02_2026-9: {to_delete_1} conversations")
print(f"strategy1_11_02_2026-Golden: {to_delete_2} conversations")
print(f"Total to delete: {to_delete_1 + to_delete_2}")

# Delete strategy1_10_02_2026-9
deleted_1 = db.query(Conversation).filter(Conversation.date_folder == 'strategy1_10_02_2026-9').delete()

# Delete strategy1_11_02_2026-Golden
deleted_2 = db.query(Conversation).filter(Conversation.date_folder == 'strategy1_11_02_2026-Golden').delete()

db.commit()

print(f"\n✅ Deleted {deleted_1} conversations from strategy1_10_02_2026-9")
print(f"✅ Deleted {deleted_2} conversations from strategy1_11_02_2026-Golden")
print(f"✅ Total deleted: {deleted_1 + deleted_2}")

# Show remaining
remaining = db.query(Conversation).count()
print(f"\n📊 Remaining conversations in database: {remaining}")

folders_after = db.query(Conversation.date_folder).distinct().all()
print(f"\nRemaining folders:")
for folder in folders_after:
    count = db.query(Conversation).filter(Conversation.date_folder == folder[0]).count()
    print(f"  {folder[0]}: {count} conversations")

print(f"\n" + "=" * 80)
print("✅ READY TO RE-IMPORT!")
print("=" * 80)
print(f"\nRun: python backend/database.py")

db.close()
