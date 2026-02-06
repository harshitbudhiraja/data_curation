# Synthetic Coding Tutor Dataset Generator

A LangGraph-based system for generating realistic student-tutor debugging conversations using autonomous LLM agents. Creates high-quality training data for fine-tuning coding tutors by simulating multi-turn debugging sessions with diverse student personalities.

## Quick Start (View Existing Data)

**New to this project? Start here to view the generated conversations:**

1. **Install dependencies**
   ```bash
   # Python backend
   pip install -r requirements.txt
   
   # Frontend (Node.js required)
   cd frontend && npm install && cd ..
   ```

2. **Start the backend**
   ```bash
   ./start_backend.sh
   ```
   Backend API runs on `http://localhost:8000`

3. **Start the frontend** (in a new terminal)
   ```bash
   ./start_frontend.sh
   ```
   UI runs on `http://localhost:5173`

4. **Browse conversations**
   - Open `http://localhost:5173` in your browser
   - Select a date folder (e.g., `strategy1_05_02_2026-2`)
   - Choose a personality or knowledge level
   - View conversations with quality ratings (gold/silver/bronze)

**The database (`backend/conversations.db`) contains pre-generated conversations from both Strategy 1 (personality-based) and Strategy 2 (knowledge-level) approaches.**

---

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

## Bug Injection System** (`simulation/agents/tutor_agent.py`)
- **Turn-based effort control**: Adjusts thoroughness and temperature by turn
- **Natural errors**: Problems are difficult enough to cause natural failures
- **Progressive refinement**: 
  - Turns 1-2: Quick initial attempt (temp=0.7, less thorough)
  - Turns 3-4: Refinement based on feedback (temp=0.5, focused)
  - Turns 5+: Complete solution (temp=0.3, very thorough)

**3. Data Pipeline**
- **Generation**: Parallel processing (5 personalities × 500 problems)
- **Dataset**: 500 curated medium-high difficulty coding questions
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

## Effort Control Strategy

### Turn-Based Progression

The tutor agent adjusts its effort level based on turn count to create natural, progressive conversations:

**Turns 1-2: Initial Attempt**
- Temperature: 0.7 (more creative/sloppy)
- Focus: Core logic without overthinking edge cases
- Result: Natural errors due to incomplete implementation

**Turns 3-4: Refinement**
- Temperature: 0.5 (more focused)
- Focus: Address specific issues from student feedback
- Result: Fixes errors while maintaining correct logic

**Turns 5+: Complete Solution**
- Temperature: 0.3 (very careful)
- Focus: Production-quality code with all edge cases
- Result: Thorough implementation that passes all tests

This creates realistic 4-8 turn conversations where student nudges actually guide the tutor's refinement process.

---

## Bug Injection Types

---

## Dataset Generation Pipeline

### 1. Setup & Sanitization
```bash
python create_dataset.py [start] [end]
# Example: python create_dataset.py 1 51  (problems 1-50)
# Example: python create_dataset.py 1 501 (all 500 problems)
```

**Dataset**: Uses 500 curated medium-high difficulty coding questions from `benchmarks/coding_questions_500.json`.

### 2. Parallel Generation
- Loads MBPP benchmark problems
- Spawns 5 processes (one per personality)
- Each process generates 100-200 conversations
- Incremental saves prevent data loss

### 3. Conversation Loop (per problem)
```
1. Student asks initial question (personality-based tone)
2. Tutor provides code with quick initial attempt (temp=0.7)
3. Execute → Natural errors due to incomplete edge case handling
4. Student points out issues based on personality
5. Tutor refines code based on feedback (temp=0.5)
6. Execute → May still have logic errors
7. Student identifies remaining issues
8. Tutor provides complete solution (temp=0.3)
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

### 6. Viewing Data in UI

**For new users who want to view existing data:**

The database (`backend/conversations.db`) contains all generated conversations. To view them:

```bash
# Terminal 1: Start backend API
./start_backend.sh
# Backend runs on http://localhost:8000

# Terminal 2: Start frontend UI
./start_frontend.sh
# Frontend runs on http://localhost:5173
```

Open `http://localhost:5173` in your browser to:
- Browse conversations by date and personality/knowledge level
- View both Strategy 1 (personality-based) and Strategy 2 (knowledge-level) data
- Filter by quality (gold/silver/bronze)
- See execution results and test outcomes
- Discard low-quality conversations

**Note**: The database already contains pre-generated conversations. You don't need to run the generation pipeline unless you want to create new data.

---

## Key Design Decisions

### Why LangGraph?
- **State management**: Tracks conversation history, execution results, turn count
- **Conditional routing**: Decides when to loop or end
- **Modularity**: Easy to add new agent types or nodes

### Why Turn-Based Effort Control?
- **Natural errors**: Problems are difficult enough to cause real failures
- **Controlled progression**: Avoids immediate solve or never solve scenarios
- **Student influence**: Nudges actually guide the refinement process
- **Realistic conversations**: 4-8 turns of genuine debugging

### Why 500 Curated Questions?
- **Medium-high difficulty**: ~10% success rate on first try
- **Appropriate challenge**: Forces multiple turns without being impossible
- **Quality over quantity**: Curated for educational value

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

### Why Turn-Based Temperature?
- Higher temp early = more creative/sloppy (natural errors)
- Lower temp later = more careful (complete solutions)
- Mimics real debugging progression

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
│   ├── mbpp.jsonl              # Original MBPP dataset (974 problems)
│   └── coding_questions_500.json  # Curated 500 medium-high difficulty questions
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
# Generate 50 conversations (problems 1-50) - good for testing
python create_dataset.py 1 51

# Generate 100 conversations (problems 1-100)
python create_dataset.py 1 101

# Generate all 500 conversations
python create_dataset.py 1 501

# Resume from problem 250
python create_dataset.py 250 501
```

### Clean Dataset
```bash
# Update INPUT_DIR and OUTPUT_DIR in clean_dataset_v2.py
python clean_dataset_v2.py
```

### Migrate to Database
```bash
# Migrates JSON files from data/ folder to SQLite database
# Supports both Strategy 1 (personality) and Strategy 2 (knowledge_level)
python backend/database.py
```

**Note**: The repository includes a pre-populated database. Only run this if you've generated new conversations or want to reload data.

### View Conversations
```bash
# Start backend (port 8000)
./start_backend.sh

# Start frontend (port 5173)
./start_frontend.sh
```

# To delete conversations from db : python delete_date_from_db.py “name of the file”
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

- `delete_date_from_db.py` - Remove conversations from database
  ```bash
  # Delete specific date folder
  python delete_date_from_db.py strategy1_05_02_2026-2
  
  # Delete ALL data (with confirmation)
  python delete_date_from_db.py --all
  ```
- `start_backend.sh` - Convenience script for backend
- `start_frontend.sh` - Convenience script for frontend

---

## License

MIT
