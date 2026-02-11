# Synthetic Coding Tutor Dataset Generator

A LangGraph-based system for generating realistic student-tutor debugging conversations using autonomous LLM agents. Creates high-quality training data for fine-tuning coding tutors by simulating multi-turn debugging sessions with diverse student personalities.

**Latest Dataset**: `strategy1_11_02_2026-Golden` contains 2,495 conversations with quality ratings (1,241 gold+silver ready for training).

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
   - Select `strategy1_11_02_2026-Golden` (latest dataset)
   - Choose a personality (Confused, Impatient, Overconfident, Programming Helper, Syntax Struggler)
   - View conversations with quality ratings:
     - 🥇 **Gold** (824): High-quality collaborative debugging
     - 🥈 **Silver** (417): Good quality with minor issues
     - 🥉 **Bronze** (1,254): Low quality (2-turn instant solutions)

**The database contains 2,495 pre-generated conversations with LLM judge quality ratings.**

---

## Overview

This system generates synthetic conversations where:
- **Student agents** (5 personalities) ask questions and provide specific, actionable feedback
- **Tutor agents** provide code solutions with intentionally incomplete early attempts
- **Execution engine** validates code against test cases using pytest
- **LLM judge** rates conversation quality (persona adherence, tutor responsiveness, dialog flow)
- **Conversations** naturally evolve through collaborative debugging (target: 6-10 turns)

The result: realistic debugging conversations that teach tutors how to handle different student behaviors and guide them through iterative problem-solving.

### Key Metrics (Golden Dataset)

| Metric | Target | Result | Status |
|--------|--------|--------|--------|
| Actionable Feedback | >70% | 94.8% | ✅ |
| Completion Rate | 60-80% | 63-77% | ✅ |
| Turn Efficiency | 6-10 avg | 4.4-5.4 avg | ⚠️ Fixed* |
| Tutor Responsiveness | >70% | 94.8% | ✅ |
| Persona Adherence | >70% | 89.8% | ✅ |

*Fixed in pipeline: Tutor now forces incomplete code in turns 1-2 to ensure minimum 4-6 turns.

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                       │
│                                                             │
│  Student → Tutor → Execute → Router → LLM Judge            │
│     ↑                           │                           │
│     └───────────────────────────┘                           │
│         (loop until solved or max turns)                    │
└─────────────────────────────────────────────────────────────┘
```

**1. Simulation Engine** (`simulation/`)
- **LangGraph state machine** orchestrates agent interactions
- **Student Agent**: Generates questions/feedback (5 personalities with specific code element references)
- **Tutor Agent**: Provides code solutions with progressive refinement
- **Execution Node**: Runs code with pytest validation
- **Router**: Decides to continue or end conversation

**2. Progressive Refinement System** (`simulation/agents/tutor_agent.py`)
- **Turn-based effort control**: Forces incomplete solutions early, complete solutions later
- **Turns 1-2**: INCOMPLETE code (max 120 tokens, temp 0.8, ignores edge cases) - MUST fail tests
- **Turns 3-4**: Gradual refinement (max 300 tokens, temp 0.6, fixes specific issues)
- **Turns 5+**: Complete solution (max 500 tokens, temp 0.3, handles all edge cases)
- **Result**: Minimum 4-6 turns of collaborative debugging

**3. Quality Verification** (`verify_conversations.py`)
- **LLM Judge** (GPT-4o-mini) rates each conversation on:
  - Persona fidelity (0-5): Does student follow their personality rules?
  - Tutor alignment (0-3): Does tutor address student feedback?
  - Dialog progression (0-2): Does conversation flow logically?
- **Quality Buckets**:
  - 🥇 Gold (8-10 points): High-quality collaborative debugging
  - 🥈 Silver (5-7 points): Good quality with minor issues
  - 🥉 Bronze (0-4 points): Low quality (auto-assigned to 2-turn instant solutions)

**4. Data Pipeline**
- **Generation**: Parallel processing (5 personalities × 500 problems)
- **Dataset**: 500 curated medium-high difficulty coding questions
- **Verification**: LLM judge scores all conversations
- **Quality Assignment**: Gold/Silver/Bronze buckets
- **Storage**: SQLite database with FastAPI backend
- **Viewing**: React frontend for browsing/filtering conversations

---

## Student Personalities

Each personality provides **specific, actionable feedback** with code element references:

| Personality | Behavior | Example Feedback |
|------------|----------|------------------|
| **CONFUSED_STUDENT** | Lost but specific | "wait i think you forgot the base case??" |
| **IMPATIENT_STUDENT** | Direct, demanding | "just add the return statement!" |
| **OVERCONFIDENT_WRONG** | Arrogant, questions tutor | "the error must be minor, maybe the test cases are wrong?" |
| **SYNTAX_STRUGGLER** | Fixated on syntax only | "is it a missing colon or bracket?" |
| **PROGRAMMING_HELPER** | Expert, provides code fixes | "The function returns wrong type. Here's the fix: return tuple(result)" |

**Key Feature**: 94.8% of student responses contain specific code element references (base case, loop, return, edge case, etc.)

---

## Progressive Refinement Strategy

### Turn-Based Code Quality Control

The tutor agent **forces incomplete code** in early turns to ensure collaborative debugging:

**Turns 1-2: INCOMPLETE First Draft (MUST FAIL)**
- Max tokens: 120 (very strict limit)
- Temperature: 0.8 (more creative/sloppy)
- Instructions: "Write 6-8 lines max, ignore edge cases, MUST fail 1-2 tests"
- Result: Incomplete code that requires student feedback

**Turns 3-4: Gradual Refinement**
- Max tokens: 300
- Temperature: 0.6 (more focused)
- Instructions: "Fix ONLY the specific issue student mentioned"
- Result: Addresses feedback but may still have issues

**Turns 5+: Complete Solution**
- Max tokens: 500
- Temperature: 0.3 (very careful)
- Instructions: "Handle ALL edge cases, pass all tests"
- Result: Production-quality code

**Impact**: Ensures minimum 4-6 turns of genuine collaborative debugging (vs 46% 2-turn instant solutions in old system).

---

## Quality Verification System

### LLM Judge Scoring

After generation, all conversations are rated by GPT-4o-mini on three dimensions:

**1. Persona Fidelity (0-5 points)**
- Does the student strictly follow their personality rules?
- Are they using appropriate language and behavior?
- Special rules per persona (e.g., Programming Helper can be verbose)

**2. Tutor Alignment (0-3 points)**
- Does the tutor's code address student feedback?
- Are modifications based on student suggestions?
- Measures genuine collaboration

**3. Dialog Progression (0-2 points)**
- Does conversation flow logically?
- No jumps or stalls?
- Natural turn-taking

**Quality Buckets** (based on total score 0-10):
- 🥇 **Gold** (8-10): High-quality collaborative debugging
- 🥈 **Silver** (5-7): Good quality with minor issues  
- 🥉 **Bronze** (0-4): Low quality or 2-turn instant solutions (auto-assigned)

**Golden Dataset Results**:
- 824 Gold (33.0%)
- 417 Silver (16.7%)
- 1,254 Bronze (50.3%)
- **1,241 usable for training** (Gold + Silver = 49.7%)

---

## Dataset Generation Pipeline

### 1. Generate Conversations
```bash
python create_dataset.py [start] [end]
# Example: python create_dataset.py 1 51  (problems 1-50)
# Example: python create_dataset.py 1 501 (all 500 problems)
```

**Dataset**: Uses 500 curated medium-high difficulty coding questions from `benchmarks/coding_questions_500.json`.

**Output**: Saves to `data/strategy1_[DATE]/[personality]_conversations.json`

### 2. Verify Quality
```bash
python verify_conversations.py
```

**Process**:
- Loads conversations from specified folder
- Calls GPT-4o-mini judge for each conversation
- Scores on persona fidelity, tutor alignment, dialog progression
- Auto-assigns Bronze to 2-turn conversations
- Saves verified conversations with scores to `verified/` subfolder

**Output**: 
- `[personality]_gold.json` (8-10 points)
- `[personality]_silver.json` (5-7 points)
- `[personality]_bronze.json` (0-4 points)
- `verification_summary.json` (statistics)

### 3. Assign Quality Buckets
```bash
python add_quality_buckets.py
```

**Process**:
- Reads verified conversations
- Adds `quality_bucket` field to each conversation
- Saves updated conversations to Golden folder

**Output**: `data/strategy1_[DATE]-Golden/` with quality_bucket field

### 4. Migrate to Database
```bash
python backend/database.py
```

Migrates JSON files to SQLite for API access. Imports `quality_bucket` field automatically.

### 5. View in UI
```bash
./start_backend.sh  # Terminal 1
./start_frontend.sh # Terminal 2
```

Browse conversations at `http://localhost:5173` with quality filters.

---

## Key Design Decisions

### Why Force Incomplete Code in Early Turns?
- **Problem**: 46% of conversations solved in just 2 turns (no collaborative learning)
- **Solution**: Strict token limits (120) + explicit instructions to ignore edge cases
- **Result**: Minimum 4-6 turns of genuine debugging where student feedback matters

### Why LLM Judge Verification?
- **Automated quality control**: Scores 2,495 conversations consistently
- **Multi-dimensional**: Persona fidelity, tutor responsiveness, dialog flow
- **Actionable buckets**: Gold/Silver for training, Bronze for filtering

### Why Specific Code Element Feedback?
- **Vague feedback doesn't help**: "something is wrong" vs "forgot base case"
- **94.8% actionable**: Students reference specific code elements
- **Tutor responsiveness**: 94.8% of tutors address the specific feedback

### Why LangGraph?
- **State management**: Tracks conversation history, execution results, turn count
- **Conditional routing**: Decides when to loop or end
- **Modularity**: Easy to add new agent types or nodes

### Why 500 Curated Questions?
- **Medium-high difficulty**: Appropriate challenge level
- **Forces multiple turns**: Not too easy (instant solve) or too hard (never solve)
- **Quality over quantity**: Curated for educational value

### Why Separate Student/Tutor Models?
- **Student**: `gpt-4o-mini` (general instruction model for natural language)
- **Tutor**: `qwen2.5-coder-7b-instruct` (specialized code model)

### Why Tone Instructions Instead of Templates?
- More flexible (LLM interprets tone naturally)
- Avoids repetitive phrasing
- Random selection adds variety

---

## Project Structure

```
.
├── simulation/
│   ├── agents/
│   │   ├── student_agent.py    # 5 personalities with specific feedback
│   │   └── tutor_agent.py      # Progressive refinement (120→300→500 tokens)
│   └── graph/
│       ├── graph.py            # LangGraph workflow assembly
│       ├── nodes.py            # Student/Tutor/Execute node wrappers
│       ├── router.py           # Conditional routing logic
│       └── state.py            # Shared state schema
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── database.py             # SQLite models + migration
│   └── conversations.db        # Pre-populated database
├── frontend/                   # React UI for browsing conversations
├── prompts/                    # System prompts for agents
├── benchmarks/
│   └── coding_questions_500.json  # Curated 500 problems
├── data/
│   ├── strategy1_11_02_2026-Golden/  # Latest dataset (2,495 conversations)
│   ├── strategy1_05_02_2026-2/       # With LLM judge scores
│   └── strategy2_04_02_2026/         # Knowledge-level strategy
├── viz_*.jpg                   # Metrics visualizations
├── create_dataset.py           # Main generation script
├── verify_conversations.py     # LLM judge verification
├── add_quality_buckets.py      # Assign gold/silver/bronze
├── clean_db_for_golden.py      # Database cleanup utility
├── llm_calling.py              # OpenRouter API integration
├── run_python.py               # Code execution with pytest
├── rate_limiter.py             # Thread-safe rate limiting


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




## Utilities

**Database Management:**
```bash
# Clean database before re-importing Golden dataset
python clean_db_for_golden.py
```

**Server Scripts:**
- `start_backend.sh` - Start FastAPI backend (port 8000)
- `start_frontend.sh` - Start React frontend (port 5173)

---
