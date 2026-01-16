# Synthetic Coding Tutor Dataset Generator

A LangGraph-based system for generating realistic student-tutor debugging conversations using autonomous LLM agents. Creates high-quality training data for fine-tuning coding tutors by simulating multi-turn debugging sessions with diverse student personalities.

## Overview

This system generates synthetic conversations where:
- **Student agents** (5 personalities) ask questions and provide feedback
- **Tutor agents** provide code solutions with intentionally injected bugs
- **Execution engine** validates code against test cases
- **Conversations** naturally evolve through debugging cycles (4-10 turns)

The result: realistic debugging conversations that teach tutors how to handle different student behaviors and common coding mistakes.

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                       │
│                                                             │
│  Student → Tutor → Execute → Router                         │
│     ↑                           │                           │
│     └───────────────────────────┘                           │
│         (loop until solved)                                 │
└─────────────────────────────────────────────────────────────┘
```

**1. Simulation Engine** (`simulation/`)
- **LangGraph state machine** orchestrates agent interactions
- **Student Agent**: Generates questions/feedback (5 personalities)
- **Tutor Agent**: Provides code solutions with bug injection
- **Execution Node**: Runs code with pytest validation
- **Router**: Decides to continue or end conversation

**2. Bug Injection System** (`simulation/agents/tutor_agent.py`)
- **20 bug types**: 10 syntax + 10 logic errors
- **Deterministic injection**: Programmatic (not LLM-generated)
- **Turn-based strategy**: Syntax bugs (turns 1-2), logic bugs (turns 3-4), correct code (turn 5+)

**3. Data Pipeline**
- **Generation**: Parallel processing (5 personalities × 200 problems)
- **Cleaning**: Remove hallucinations, LLM artifacts, false failures
- **Storage**: SQLite database with FastAPI backend
- **Viewing**: React frontend for browsing/filtering conversations

---

## Student Personalities

Each personality uses **tone instructions** to guide LLM behavior:

| Personality | Behavior | Example |
|------------|----------|---------|
| **CONFUSED_STUDENT** | Lost, asks basic questions | "wait i think you're returning a list but it should be a tuple?" |
| **IMPATIENT_STUDENT** | Direct, demands quick fixes | "that failed, just fix it please" |
| **OVERCONFIDENT_WRONG** | Arrogant, questions tutor | "the error must be minor, maybe the test cases are wrong?" |
| **SYNTAX_STRUGGLER** | Fixated on syntax errors | "is it a missing colon or bracket?" |
| **PROGRAMMING_HELPER** | Professional, collaborative | "I see the issue - you used \| instead of & for intersection" |

---

## Bug Injection Types

### Syntax Bugs (Turns 1-2)
1. `remove_colon` - Missing `:` in function definition
2. `missing_paren_def` - Missing `)` in parameters
3. `missing_paren_return` - Missing `)` in return statement
4. `missing_open_paren` - Missing `(` 
5. `extra_comma` - Double comma in parameters
6. `missing_equals` - Missing `=` in assignment
7. `typo_def` - `deff` instead of `def`
8. `typo_return` - `retrun` instead of `return`
9. `missing_bracket` - Missing `]`
10. `wrong_indent` - Incorrect indentation

### Logic Bugs (Turns 3-4)
1. `intersection_to_union` - `&` → `|` in sets
2. `union_to_intersection` - `|` → `&` in sets
3. `remove_set` - Missing `set()` wrapper
4. `remove_tuple` - Missing `tuple()` wrapper
5. `list_to_tuple` - Wrong type conversion
6. `remove_sorted` - Missing `sorted()` call
7. `flip_equals` - `==` → `!=`
8. `in_to_not_in` - `in` → `not in`
9. `off_by_one` - Range offset error
10. `wrong_var` - Wrong variable name

---

## Dataset Generation Pipeline

### 1. Setup & Sanitization
```bash
python create_dataset.py [start] [end]
# Example: python create_dataset.py 1 101  (problems 1-100)
```

**Sanitization**: Renames `test_*` functions to `check_*` to prevent pytest naming collisions.

### 2. Parallel Generation
- Loads MBPP benchmark problems
- Spawns 5 processes (one per personality)
- Each process generates 100-200 conversations
- Incremental saves prevent data loss

### 3. Conversation Loop (per problem)
```
1. Student asks initial question (personality-based tone)
2. Tutor provides code with syntax bug
3. Execute → Syntax error
4. Student points out syntax error
5. Tutor provides code with logic bug
6. Execute → Logic error (tests fail)
7. Student identifies logic issue
8. Tutor provides correct code
9. Execute → All tests pass ✅
10. END
```

### 4. Post-Processing
```bash
python clean_dataset_v2.py
```

**Filters:**
- ✅ Must be solved (all tests pass)
- ❌ Remove hallucinations (tutor roleplaying as student)
- 🚑 Rescue false failures (trust test results over flags)

**Cleaning:**
- Remove LLM artifacts (`<|tokens|>`, `<think>` tags)
- Remove style instructions leaking into output
- Regenerate UUIDs

### 5. Database Migration
```bash
python backend/database.py
```
Migrates JSON files to SQLite for API access.

### 6. Viewing
```bash
# Terminal 1: Start backend
./start_backend.sh

# Terminal 2: Start frontend
./start_frontend.sh
```
Browse conversations at `http://localhost:5173`

---

## Key Design Decisions

### Why LangGraph?
- **State management**: Tracks conversation history, execution results, turn count
- **Conditional routing**: Decides when to loop or end
- **Modularity**: Easy to add new agent types or nodes

### Why Inject Bugs Programmatically?
- **LLMs are bad at generating bugs on command** (they try to fix them)
- **Deterministic bugs** ensure quality and consistency
- **Guarantees minimum 4 turns** for realistic debugging conversations

### Why Separate Student/Tutor Models?
- **Student**: `qwen-2.5-7b-instruct` (general instruction model for natural language)
- **Tutor**: `qwen2.5-coder-7b-instruct` (specialized code model)

### Why Tone Instructions Instead of Templates?
- More flexible (LLM interprets tone naturally)
- Avoids repetitive phrasing
- Random selection adds variety

### Why Aggressive Code Extraction?
- LLMs leak prompts, explanations, wrapper tags
- Need pure code for execution
- Regex-based extraction with multiple fallbacks

---

## Project Structure

```
.
├── simulation/
│   ├── agents/
│   │   ├── student_agent.py    # 5 personality types with tone instructions
│   │   └── tutor_agent.py      # Code generation + bug injection
│   └── graph/
│       ├── graph.py            # LangGraph workflow assembly
│       ├── nodes.py            # Student/Tutor/Execute node wrappers
│       ├── router.py           # Conditional routing logic
│       └── state.py            # Shared state schema
├── backend/
│   ├── main.py                 # FastAPI server
│   └── database.py             # SQLite models + migration
├── frontend/                   # React UI for browsing conversations
├── prompts/                    # System prompts for agents
├── benchmarks/
│   └── mbpp.jsonl              # MBPP dataset (974 problems)
├── data/                       # Generated conversations (by date)
├── create_dataset.py           # Main generation script
├── clean_dataset_v2.py         # Post-processing pipeline
├── llm_calling.py              # OpenRouter API integration
├── run_python.py               # Code execution with pytest
└── rate_limiter.py             # Thread-safe rate limiting

```

---

## Requirements

- Python 3.8+
- OpenRouter API key (set in `.env`)
- Node.js 16+ (for frontend)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install
```

---

## Usage

### Generate Dataset
```bash
# Generate 100 conversations (problems 1-100)
python create_dataset.py 1 101

# Resume from problem 50
python create_dataset.py 50 101
```

### Clean Dataset
```bash
# Update INPUT_DIR and OUTPUT_DIR in clean_dataset_v2.py
python clean_dataset_v2.py
```

### Migrate to Database
```bash
python backend/database.py
```

### View Conversations
```bash
# Start backend (port 8000)
./start_backend.sh

# Start frontend (port 5173)
./start_frontend.sh
```

---

## Output Format

Each conversation is stored as JSON:

```json
{
  "id": "uuid",
  "task_id": 19,
  "personality": "CONFUSED_STUDENT",
  "problem_text": "Write a function to find duplicate elements...",
  "test_cases": ["assert check_duplicate([1,2,3]) == False", ...],
  "conversation": [
    {
      "role": "student",
      "content": "hey can you help with check_duplicate?",
      "turn": 1
    },
    {
      "role": "tutor",
      "content": "def check_duplicate(arr):\n    return len(arr) != len(set(arr)",
      "turn": 2,
      "execution": {
        "success": false,
        "tests_passed": 0,
        "total_tests": 3,
        "error_type": "syntax_error",
        "message": "SyntaxError: invalid syntax"
      }
    }
  ],
  "solved": true,
  "tests_passed": 3,
  "total_tests": 3,
  "turns": 6
}
```

---

## API Endpoints

- `GET /api/dates` - List available date folders
- `GET /api/personalities/{date}` - List personalities for date
- `GET /api/conversations/{date}/{personality}` - List conversations
- `GET /api/conversation/{id}` - Get full conversation details
- `PATCH /api/conversations/{id}/discard` - Toggle discard status
- `GET /api/stats/{date}/{personality}` - Get statistics

---

## Utilities

- `delete_date_from_db.py` - Remove conversations from specific date
- `start_backend.sh` - Convenience script for backend
- `start_frontend.sh` - Convenience script for frontend

---

## License

MIT
