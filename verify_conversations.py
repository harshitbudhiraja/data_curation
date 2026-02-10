"""Verify conversation quality using GPT-4o-mini as judge."""
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-4o-mini"
INPUT_DIR = "data/strategy1_10_02_2026-7"
OUTPUT_DIR = f"{INPUT_DIR}/verified"

os.makedirs(OUTPUT_DIR, exist_ok=True)

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def load_persona_rules():
    """Load persona rules from prompt files."""
    persona_files = {
        'CONFUSED_STUDENT': 'prompts/confused_student.txt',
        'IMPATIENT_STUDENT': 'prompts/impatient_student.txt',
        'OVERCONFIDENT_WRONG': 'prompts/overconfident_wrong.txt',
        'SYNTAX_STRUGGLER': 'prompts/syntax_struggler.txt',
        'PROGRAMMING_HELPER': 'prompts/programming_helper.txt'
    }
    
    rules = {}
    for persona, filepath in persona_files.items():
        with open(filepath, 'r') as f:
            rules[persona] = f.read()
    
    return rules

PERSONA_RULES = load_persona_rules()

JUDGE_PROMPT_TEMPLATE = """You are an evaluator judging a persona-based student–tutor coding conversation.

IMPORTANT:
- Errors are natural (temperature-driven).
- Student follows a STRICT persona.
- Tutor outputs ONLY code.
- Judge BEHAVIOR, not correctness.

PERSONA RULES FOR THIS CONVERSATION:
{persona_rules}

SPECIAL SCORING RULES BY PERSONA:
- PROGRAMMING_HELPER: Being verbose and providing detailed code fixes is CORRECT behavior. Do NOT penalize for length or technical detail. They should provide complete working code fixes.
- SYNTAX_STRUGGLER: Should ONLY talk about syntax (colons, brackets, indentation). Penalize heavily if they discuss logic/algorithms.
- CONFUSED_STUDENT: Should be brief and confused. Penalize if they sound knowledgeable.
- IMPATIENT_STUDENT: Should be demanding and brief. Penalize if they're polite or patient.
- OVERCONFIDENT_WRONG: Should be cocky and suggest wrong fixes. Penalize if they're uncertain or correct.

Evaluate:
1. Persona fidelity (0–5): Does the student strictly follow their persona rules? (Consider persona-specific expectations above)
2. Tutor alignment (0–3): Does the tutor's CODE attempt to address the issues mentioned by the student or test failures? (Tutor only outputs code, no explanations needed)
3. Dialog progression (0–2): Do turns logically follow without jumps or stalls?

Bucket rules: 8–10 = gold, 5–7 = silver, 0–4 = bronze

Return ONLY JSON (no markdown):
{{
  "persona_fidelity": 0-5,
  "tutor_alignment": 0-3,
  "dialog_progression": 0-2,
  "total_score": 0-10,
  "bucket": "gold|silver|bronze",
  "needs_human_review": true|false,
  "main_failure": "persona_break|tutor_misaligned|dialog_stall|none"
}}

Conversation:
{conversation}
"""

def format_conversation(conversation_array):
    """Format conversation array into readable text."""
    lines = []
    for msg in conversation_array:
        role = msg['role'].upper()
        content = msg['content']
        turn = msg['turn']
        
        if role == 'TUTOR' and 'execution' in msg:
            exec_result = msg['execution']
            if exec_result['success']:
                exec_info = f" [✓ All tests passed]"
            else:
                exec_info = f" [✗ {exec_result['tests_passed']}/{exec_result['total_tests']} tests]"
            lines.append(f"Turn {turn} - {role}:{exec_info}\n{content}\n")
        else:
            lines.append(f"Turn {turn} - {role}:\n{content}\n")
    
    return "\n".join(lines)

def judge_conversation(conversation_obj):
    """Call GPT-4o-mini to judge a conversation."""
    persona = conversation_obj['personality']
    conversation_text = format_conversation(conversation_obj['conversation'])
    persona_rules = PERSONA_RULES.get(persona, "No rules found")
    
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        persona_rules=persona_rules,
        conversation=conversation_text
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        verdict = json.loads(content)
        return verdict
    
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return {
            "persona_fidelity": 0,
            "tutor_alignment": 0,
            "dialog_progression": 0,
            "total_score": 0,
            "bucket": "bronze",
            "needs_human_review": True,
            "main_failure": "error"
        }

def process_persona_file(filepath, persona_name):
    """Process all conversations for one persona."""
    print(f"\n{'='*80}")
    print(f"Processing: {persona_name}")
    print(f"{'='*80}")
    
    with open(filepath, 'r') as f:
        conversations = json.load(f)
    
    gold, silver, bronze = [], [], []
    
    for i, convo in enumerate(conversations):
        print(f"  [{i+1}/{len(conversations)}] task_id={convo['task_id']}...", end=" ")
        
        verdict = judge_conversation(convo)
        
        record = {
            "id": convo['id'],
            "task_id": convo['task_id'],
            "personality": convo['personality'],
            "conversation": convo['conversation'],
            "solved": convo.get('solved', False),
            "turns": convo.get('turns', 0),
            "scores": verdict
        }
        
        bucket = verdict['bucket']
        if bucket == 'gold':
            gold.append(record)
        elif bucket == 'silver':
            silver.append(record)
        else:
            bronze.append(record)
        
        print(f"{bucket.upper()} ({verdict['total_score']})")
    
    base_name = persona_name.lower().replace(' ', '_')
    json.dump(gold, open(f"{OUTPUT_DIR}/{base_name}_gold.json", "w"), indent=2)
    json.dump(silver, open(f"{OUTPUT_DIR}/{base_name}_silver.json", "w"), indent=2)
    json.dump(bronze, open(f"{OUTPUT_DIR}/{base_name}_bronze.json", "w"), indent=2)
    
    print(f"\n  ✅ {len(gold)} gold, {len(silver)} silver, {len(bronze)} bronze")
    
    return {
        "total": len(conversations),
        "gold": len(gold),
        "silver": len(silver),
        "bronze": len(bronze),
        "gold_rate": f"{len(gold)/len(conversations)*100:.1f}%"
    }

def main():
    print("\n" + "="*80)
    print("CONVERSATION QUALITY VERIFICATION")
    print("="*80)
    
    persona_files = {
        'Confused Student': f'{INPUT_DIR}/confused_student_conversations.json',
        'Impatient Student': f'{INPUT_DIR}/impatient_student_conversations.json',
        'Overconfident Wrong': f'{INPUT_DIR}/overconfident_wrong_conversations.json',
        'Programming Helper': f'{INPUT_DIR}/programming_helper_conversations.json',
        'Syntax Struggler': f'{INPUT_DIR}/syntax_struggler_conversations.json'
    }
    
    all_stats = {}
    
    for persona_name, filepath in persona_files.items():
        stats = process_persona_file(filepath, persona_name)
        all_stats[persona_name] = stats
    
    total_convos = sum(s['total'] for s in all_stats.values())
    total_gold = sum(s['gold'] for s in all_stats.values())
    total_silver = sum(s['silver'] for s in all_stats.values())
    total_bronze = sum(s['bronze'] for s in all_stats.values())
    
    summary = {
        "total_conversations": total_convos,
        "overall": {
            "gold": total_gold,
            "silver": total_silver,
            "bronze": total_bronze,
            "gold_rate": f"{total_gold/total_convos*100:.1f}%"
        },
        "by_persona": all_stats
    }
    
    with open(f"{OUTPUT_DIR}/verification_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"\nTotal: {total_convos}")
    print(f"  🥇 GOLD:   {total_gold} ({summary['overall']['gold_rate']})")
    print(f"  🥈 SILVER: {total_silver} ({total_silver/total_convos*100:.1f}%)")
    print(f"  🥉 BRONZE: {total_bronze} ({total_bronze/total_convos*100:.1f}%)")
    print(f"\n✅ Results saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
