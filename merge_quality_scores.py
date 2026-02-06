"""Merge quality verification scores back into main conversation JSON files."""
import json
import os
from pathlib import Path

def merge_quality_scores(data_dir):
    """Merge quality scores from verified/ folder back into main JSON files.
    
    Args:
        data_dir: Path to data directory (e.g., "data/strategy1_05_02_2026-2")
    """
    data_path = Path(data_dir)
    verified_path = data_path / "verified"
    
    if not verified_path.exists():
        print(f"❌ No verified/ folder found in {data_dir}")
        return
    
    print(f"\n{'='*80}")
    print(f"MERGING QUALITY SCORES: {data_dir}")
    print(f"{'='*80}\n")
    
    # Map conversation IDs to quality buckets
    quality_map = {}
    
    # Read all verified files
    for quality in ['gold', 'silver', 'bronze']:
        for verified_file in verified_path.glob(f"*_{quality}.json"):
            with open(verified_file, 'r') as f:
                conversations = json.load(f)
            
            for conv in conversations:
                quality_map[conv['id']] = {
                    'bucket': quality,
                    'scores': conv['scores']
                }
            
            print(f"  📂 Loaded {len(conversations)} {quality} conversations from {verified_file.name}")
    
    print(f"\n  ✅ Total quality scores loaded: {len(quality_map)}")
    
    # Update main conversation files
    persona_files = [
        'confused_student_conversations.json',
        'impatient_student_conversations.json',
        'overconfident_wrong_conversations.json',
        'programming_helper_conversations.json',
        'syntax_struggler_conversations.json'
    ]
    
    total_updated = 0
    
    for filename in persona_files:
        filepath = data_path / filename
        
        if not filepath.exists():
            continue
        
        # Read conversations
        with open(filepath, 'r') as f:
            conversations = json.load(f)
        
        # Add quality scores
        updated_count = 0
        for conv in conversations:
            conv_id = conv['id']
            if conv_id in quality_map:
                conv['quality_bucket'] = quality_map[conv_id]['bucket']
                conv['quality_scores'] = quality_map[conv_id]['scores']
                updated_count += 1
        
        # Save updated file
        with open(filepath, 'w') as f:
            json.dump(conversations, f, indent=2)
        
        print(f"  ✅ Updated {updated_count}/{len(conversations)} in {filename}")
        total_updated += updated_count
    
    print(f"\n{'='*80}")
    print(f"✅ MERGE COMPLETE: {total_updated} conversations updated with quality scores")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import sys
    
    # Default to most recent strategy folder
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/strategy1_05_02_2026-2"
    merge_quality_scores(data_dir)
