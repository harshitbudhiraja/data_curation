#!/usr/bin/env python3
"""Add quality_bucket field to conversation JSON files from verified folder."""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


def add_quality_tags(conversations_file, verified_folder):
    """Add quality_bucket to conversations based on verified files."""
    print(f"\n📁 Processing: {conversations_file}")
    
    # Backup disabled - user request
    # backup_file = conversations_file.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    # shutil.copy(conversations_file, backup_file)
    # print(f"✅ Backup created: {backup_file}")
    
    # Load conversations
    with open(conversations_file) as f:
        conversations = json.load(f)
    print(f"✅ Loaded {len(conversations)} conversations")
    
    # Extract personality name from filename (e.g., "confused_student_conversations.json" -> "confused_student")
    personality = Path(conversations_file).stem.replace('_conversations', '')
    
    # Load verified files for this personality
    quality_map = {}
    
    for bucket in ['gold', 'silver', 'bronze']:
        verified_file = verified_folder / f"{personality}_{bucket}.json"
        if verified_file.exists():
            with open(verified_file) as f:
                verified_convs = json.load(f)
                for conv in verified_convs:
                    quality_map[conv['id']] = bucket
            print(f"✅ Loaded {len(verified_convs)} {bucket} conversations")
    
    print(f"✅ Total verified: {len(quality_map)} conversations")
    
    # Add quality_bucket to each conversation
    updated_count = 0
    for conv in conversations:
        conv_id = conv['id']
        if conv_id in quality_map:
            conv['quality_bucket'] = quality_map[conv_id]
            updated_count += 1
    
    print(f"✅ Added quality_bucket to {updated_count}/{len(conversations)} conversations")
    
    # Count by quality
    gold = sum(1 for c in conversations if c.get('quality_bucket') == 'gold')
    silver = sum(1 for c in conversations if c.get('quality_bucket') == 'silver')
    bronze = sum(1 for c in conversations if c.get('quality_bucket') == 'bronze')
    unverified = len(conversations) - (gold + silver + bronze)
    
    print(f"   🥇 GOLD:   {gold}")
    print(f"   🥈 SILVER: {silver}")
    print(f"   🥉 BRONZE: {bronze}")
    if unverified > 0:
        print(f"   ⚪ UNVERIFIED: {unverified}")
    
    # Save updated conversations
    with open(conversations_file, 'w') as f:
        json.dump(conversations, f, indent=2)
    print(f"✅ Saved updated file: {conversations_file}")
    
    return updated_count, gold, silver, bronze


def main():
    # Get date folder from command line or use latest
    if len(sys.argv) > 1:
        date_folder = sys.argv[1]
    else:
        # Find latest strategy1 folder
        data_dir = Path('data')
        folders = [f for f in data_dir.iterdir() if f.is_dir() and f.name.startswith('strategy1_')]
        if not folders:
            print("❌ No strategy1 folders found in data/")
            return
        date_folder = sorted(folders)[-1].name
        print(f"📂 Using latest folder: {date_folder}")
    
    data_path = Path('data') / date_folder
    verified_path = data_path / 'verified'
    
    if not verified_path.exists():
        print(f"❌ Verified folder not found: {verified_path}")
        return
    
    print("=" * 80)
    print("🏷️  ADDING QUALITY TAGS TO CONVERSATIONS")
    print("=" * 80)
    print(f"📂 Data folder: {data_path}")
    print(f"📂 Verified folder: {verified_path}")
    
    personalities = [
        'confused_student',
        'impatient_student',
        'overconfident_wrong',
        'programming_helper',
        'syntax_struggler'
    ]
    
    total_updated = 0
    total_gold = 0
    total_silver = 0
    total_bronze = 0
    
    for personality in personalities:
        conversations_file = data_path / f"{personality}_conversations.json"
        
        if not conversations_file.exists():
            print(f"\n⚠️  Skipping {personality}: file not found")
            continue
        
        print(f"\n{'='*80}")
        print(f"📋 Processing: {personality.replace('_', ' ').title()}")
        print(f"{'='*80}")
        
        updated, gold, silver, bronze = add_quality_tags(
            str(conversations_file),
            verified_path
        )
        
        total_updated += updated
        total_gold += gold
        total_silver += silver
        total_bronze += bronze
    
    print("\n" + "=" * 80)
    print("🎉 QUALITY TAGS ADDED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\n✅ Total conversations updated: {total_updated}")
    print(f"\n📊 Quality Distribution:")
    print(f"   🥇 GOLD:   {total_gold} ({total_gold/total_updated*100:.1f}%)")
    print(f"   🥈 SILVER: {total_silver} ({total_silver/total_updated*100:.1f}%)")
    print(f"   🥉 BRONZE: {total_bronze} ({total_bronze/total_updated*100:.1f}%)")
    print(f"\n📁 Updated files in: {data_path}")
    for personality in personalities:
        print(f"   - {personality}_conversations.json")
    print(f"\n✅ Ready to migrate to database!")
    print(f"   Run: python backend/database.py")


if __name__ == '__main__':
    main()
