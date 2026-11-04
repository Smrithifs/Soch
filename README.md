# Soch
# SOCH — Agentic DSA Learning & Interview Preparation Platform

> *"Soch"* (सोच) means **thought** — SOCH helps students *think* through problems, remember what they learn, and walk into OAs and interviews prepared.

SOCH is a full-stack web app that gives every student a **personal DSA coach**. It knows:

- **who you are**: track, company, deadline, level, daily time
- **what you've done**: real code submissions, test results, mistakes
- **what you're forgetting**: a per-topic forgetting curve

From that it decides **what you should do today**. Five AI agents, orchestrated with **LangGraph**, run on a **local language model** (no API key, no cost, your data never leaves your laptop). Code is **compiled and run for real**, and verdicts are never faked.

---

## Contents
1. [The problem](#1-the-problem)
2. [What SOCH does](#2-what-soch-does)
3. [Tech stack](#3-tech-stack)
4. [Architecture](#4-architecture)
5. [The agents](#5-the-agents)
6. [The memory model (forgetting curve)](#6-the-memory-model-forgetting-curve)
7. [Personalization rules](#7-personalization-rules)
8. [Code execution](#8-code-execution)
9. [Features page by page](#9-features-page-by-page)
10. [Database design](#10-database-design)
11. [API reference](#11-api-reference)
12. [Project structure](#12-project-structure)
13. [Setup & run (macOS)](#13-setup--run-macos)
14. [Demo script](#14-demo-script)
15. [Testing](#15-testing)
16. [Design decisions & limitations](#16-design-decisions--limitations)
17. [Agent orchestration & automation: LangGraph & n8n](#17-agent-orchestration--automation-langgraph--n8n)

---

## 1. The problem

Students preparing for DSA, online assessments (OAs) and interviews hit the same walls:

| Pain | What actually happens |
|---|---|
| **Random practice** | They solve whatever LeetCode shows next, not what *their* OA or *their* gaps need. |
| **Forgetting** | *"I solved DP yesterday, today I can't even start."* Newly learned material fades within a day if it isn't retrieved. |
| **Breaks** | After a week off, they don't know where to restart, so they restart from scratch or give up. |
| **No feedback loop** | A Wrong Answer says *that* code failed, not *why* their thinking was wrong. |
| **Interview nerves** | Knowing the solution ≠ explaining it clearly, with complexity and edge cases, to a person. |

## 2. What SOCH does

| Capability | How |
|---|---|
| **Personalised onboarding** | Three tracks (**OA**, **Interviews**, **DSA Learning**), each asking different questions (company, deadline, number of questions, starting topic, months available, daily minutes…). |
| **Daily plan that fits your time** | A deterministic rule engine builds today's plan from your track, deadline, minutes, memory and mistakes. Change 15 → 10 → 5 minutes and the plan recalculates instantly, with a reason for every task. |
| **AI tutor that reads your code** | Explains *your* bug using *your* real failing test case, gives progressive hints, analyses *your* complexity. |
| **Forgetting curve + Recall Rescue** | Every topic decays over time. When a topic you solved is "forgotten", the Recall Coach pulls it back out of your memory step by step instead of showing you the answer. |
| **Catch-up after a break** | After days away, the Catch-up Planner rebuilds today around what decayed most. |
| **Mock OA with review** | A timed multi-question OA, one final submission, and a review per question (where it went wrong, what went well, how to fix it). Weak topics are pushed into your roadmap automatically. |
| **Interview simulator with a speaking interviewer** | "Ananya", an illustrated AI interviewer, asks questions aloud, listens (type or speak), reacts, asks follow-ups and produces a scored feedback report. |
| **Mistake DNA** | Every mistake is classified (logic, edge case, complexity, recall, communication…) and linked to its problem, revision card and next problem. |
| **Smart Revision** | Spaced-repetition cards, including *"predict the output"* code cards. |
| **Calendar** | A real month view; click any day to see exactly what you'll do (live today, projected future, history past). |
| **Company preparation** | Company-specific focus topics, readiness %, and an agent-written game plan personalised to your memory and deadline. |
| **Agent Console** | Full transparency: every agent decision shows what it observed → what it decided → which model answered. |

---

## 3. Tech stack

### Frontend
| Technology | Why it's used |
|---|---|
| **React 18 + TypeScript** | Component-based UI with type safety across 15 pages. |
| **Vite** | Fast dev server and build; proxies `/api` to the backend. |
| **Tailwind CSS v4** | Utility-first styling for the dark, developer-tool aesthetic (Linear/Vercel/Raycast-inspired). |
| **Monaco Editor** (`@monaco-editor/react`) | The VS Code editor: Java/Python highlighting, bundled locally so it works offline. |
| **React Flow** (`@xyflow/react`) | Interactive ThinkMap: clickable, expandable, zoomable problem-solving graph. |
| **Recharts** | Forgetting curves, XP charts, mastery bars, interview radar chart. |
| **Lucide React** | Icon set. |
| **React Router** | Page routing. |
| **Web Speech API** (browser built-in) | The interviewer's voice (`speechSynthesis`) and voice answers (`SpeechRecognition`). No external service. |

### Backend
| Technology | Why it's used |
|---|---|
| **Python 3.12** | Main backend language. |
| **FastAPI** | REST API with automatic validation and docs (`/docs`). |
| **Pydantic v2** | Request/response validation (e.g. minutes must be 5–240, valid track names). |
| **SQLAlchemy 2** | ORM over SQLite; business logic stays in service modules. |
| **SQLite** | Single-file database (`backend/soch.db`); survives refreshes and restarts. |
| **httpx** | HTTP client for the local LLM (Ollama) and optional Judge0. |
| **Uvicorn** | ASGI server. |

### AI / LLM
| Technology | Why it's used |
|---|---|
| **Ollama** | Runs open-source language models locally on the Mac (Apple Silicon GPU via Metal). |
| **Qwen 2.5 (3B / 7B)** | The default model: good instruction following and JSON output at a size that fits a MacBook Air. |
| **Rule-based fallback** | Every agent has a deterministic fallback, so the app never breaks if the model is off. Each answer is labelled **✦ agent** or **offline rules**. |

### Code execution
| Technology | Why it's used |
|---|---|
| **OpenJDK 21 (`javac` / `java`)** | Real compilation and execution of student Java code in a local sandbox. |
| **Python 3** | Python solutions run the same way. |
| **Judge0** (optional) | Remote sandboxed execution if `JUDGE0_URL` is set. |

### Orchestration & automation (see §17)
| Technology | Role |
|---|---|
| **LangGraph** | Stateful agent graphs: Recall Coach ladder, Catch-up Planner, supervisor routing between agents, checkpointed sessions. |
| **LangChain-Ollama** | Model wrapper used by LangGraph nodes (same local Qwen model). |
| **n8n** | Workflow automation outside the app: daily reminders, weekly reports, post–Mock OA notifications. |

### Testing
| Technology | Why it's used |
|---|---|
| **FastAPI TestClient** | End-to-end API tests with real SQLite and real Java. |
| **Fake Ollama server** | Verifies the agent plumbing (prompt → JSON → validation → DB) without a real model. |
| **Playwright** | Browser walkthroughs used during development. |

---

## 4. Architecture

```
┌──────────────────────────── Browser (React + Vite, :5173) ────────────────────────────┐
│ Sign-up · Dashboard · Practice Arena (Monaco) · Memory · Calendar · Mock OA ·          │
│ Interview (avatar + voice) · Revision · Mistake DNA · Company · Agent Console …        │
└──────────────────────────────────────┬─────────────────────────────────────────────────┘
                                       │ REST /api/*  (JSON)
┌──────────────────────────────────────▼─────────────────────────────────────────────────┐
│ FastAPI (:8000)  api/routes.py — validation, transactions, per-student virtual clock    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ services/                                                                               │
│  personalization_engine  → time budget, problem scoring, daily plan, XP/streak          │
│  memory_model            → forgetting curve per topic (R = e^(−t/S))                    │
│  agents / graphs (LangGraph) → Coach · Tutor · Recall Coach · Catch-up · Interviewer    │
│  features                → Company coach · Calendar day plans · Mock OA reviewer        │
│  learning_services       → spaced repetition · mistake classification · analytics       │
│  tutor_engine            → static code analysis · bug detectors · offline answers       │
│  executor                → javac/java sandbox (or Judge0) · per-test grading            │
│  llm                     → Ollama client · auto model detection · JSON parsing          │
│  clock                   → per-student time travel for demos                            │
└───────────────┬───────────────────────────────┬────────────────────────────────────────┘
                │                               │
        ┌───────▼────────┐             ┌────────▼─────────┐        ┌──────────────────────┐
        │ SQLite soch.db │             │ Ollama (:11434)  │        │ javac / java sandbox │
        │ 13 tables      │             │ qwen2.5 local LLM│        │ temp dir + timeouts  │
        └────────────────┘             └──────────────────┘        └──────────────────────┘
```

### The agent loop (how every agent works)
```
 OBSERVE  →  gather the student's REAL state (profile, memory curve, code, compiler results, mistakes)
 THINK    →  local LLM reasons over that context under a strict output contract (often JSON)
 VALIDATE →  server checks the output (only real task ids, minutes fit the budget, scores 0–10 …)
 ACT      →  write to plan / memory / mistakes / chat
 TRACE    →  store observed + decided + model + latency in agent_runs → visible in Agent Console
 FALLBACK →  if the model is offline or returns junk → deterministic rules, labelled "offline rules"
```

### Key design principle: the LLM never decides facts
- **Pass/fail** comes only from the real compiler.
- **Memory decay** is a formula, not a guess.
- **Time budgets** are explicit rules.
- The LLM handles what humans are good at: **explaining, coaching, judging free-text answers, planning with reasons**.

---

## 5. The agents

| Agent | Trigger | Observes | Does |
|---|---|---|---|
| **Coach** | Opening the dashboard | Memory per topic, today's plan, open mistakes, streak | Writes a 3-sentence daily brief: what matters most today and why. |
| **Tutor** | Any question / button in the Practice Arena | Your current code, static analysis (loops, data structures, Big-O), **real** latest test result, known bug patterns, hints used, topic retention, chat history | Socratic help: diagnoses your bug using your failing test, gives the next hint only, analyses *your* complexity. Won't paste a full solution unless asked. |
| **Recall Coach** | "Recall Rescue" (dashboard / memory page / plan) | Topic retention, days since last solved, the problem's key insight, your answer at each step | A 6-step retrieval ladder: **Cue → Trigger → State → Transition → Base & order → Rebuild**. Wrong answers get a *smaller cue*, never the answer. The final step only passes after a **real Accepted submission**. Then it strengthens memory and schedules tomorrow's review. |
| **Catch-up Planner** | After a gap (e.g. 10 days away) | Days away, retention per topic, deadline, minutes available, candidate tasks with ids | Chooses and orders today's tasks: recall forgotten topics first, then fading ones, then deadline work. Every chosen id is validated and the total must fit your minutes. |
| **Interviewer ("Ananya")** | Interview Simulator | Each answer + rubric + reference solution; your **real** submission for "code correctness" | Grades each answer 0–10, gives specific feedback, asks follow-up probes, produces a full report (strengths, weaknesses, recommendations, change vs baseline). |
| **OA Reviewer** | Mock OA final submission | Your code, **real** test results per question, static analysis, bug patterns | Per-question review: where it went wrong, what went well, how to fix it, concept gap. Weak topics → roadmap. |
| **Company Coach** | Company Preparation page | Company, stage, days left, memory on the company's focus topics | A personalised game plan for that company. |

All prompts live in `backend/services/agents.py` and `features.py`.

---

## 6. The memory model (forgetting curve)

Each student × topic has a **stability S** (in days) and a **last review time**.

```
Retention   R(t) = e^(−t / S)           t = days since last successful review

After a review:
  strong  (solved unaided / recalled correctly)   S ← S × (1.5 + 2·(1 − R))   ← spacing effect
  weak    (solved with hints / recall needed help) S ← S × 1.2
  fail    (couldn't solve something solved before) S ← max(0.3, S × 0.5)

First solve:  S = 1.2 days  →  next day R ≈ 43%  ("I did DP yesterday, I'm blank today")
Bands:        strong ≥ 75%   ·   fading 45–75%   ·   forgotten < 45%
```

**Why the spacing effect matters:** reviewing a topic when it's half-forgotten (low R) multiplies stability far more than cramming it while fresh. So SOCH schedules recall *just as things fade*.

**Time travel (demo):** the sidebar's **+1d / +3d / +10d** buttons move a per-student virtual clock (`services/clock.py`). Memory decay, countdowns, streaks, due cards and plans all move together, so you can *show* forgetting and catch-up live.

---

## 7. Personalization rules

Implemented in `services/personalization_engine.py`. They are explicit, testable and non-random.

### Time budget
| Available time | Plan |
|---|---|
| **< 8 min** | Revision only (up to 3 recall cards). |
| **8–19 min** | 1 coding problem (8–9 min) + revision cards. |
| **≥ 20 min, OA** | `min(questions_expected, (minutes − 5) ÷ 10)` timed problems + 1 short revision. |
| **≥ 20 min, Interview ≤ 7 days away** | Revision-heavy: 1 problem + recall cards + 1 communication drill. |
| **≥ 20 min, Learning** | 1 problem (2 if ≥ 35 min) + prerequisite revision. |
| **Any topic in "forgotten"** | Today opens with a **Recall Rescue** before new work. |

### Problem selection (scored, deterministic)
```
score = 10  if it covers a priority topic (forgotten > fading > open mistakes > declared weak > current topic)
      + company weight (0–5)
      + track frequency (OA pattern frequency / interview frequency)
      + 50  if previously failed (interview track — retry first)
      + learning-path order bonus (learning track)
      − 30  if already solved
ties broken alphabetically → same profile, same plan, every time
```

### Spaced repetition (cards)
- Correct → interval 1 → 3 → 7 → 14 → 30 days.
- Wrong → due again in **10 minutes**, a **Concept Recall Error** is recorded, and the topic is marked "needs revision".
- Priority considers due time, last result, open mistakes, mastery, hint usage and accuracy.

---

## 8. Code execution

`services/executor.py`
- Student code + a hidden **driver** (`Main` class that parses stdin and calls `Solution`) is written to a temp directory.
- `javac` compiles it. A failure is a **Compilation Error** with the real compiler message.
- Each test runs `java` with a **4 s timeout**, a **256 MB heap** cap, a clean environment and an isolated directory.
- Output is compared to the expected value, giving **Accepted / Wrong Answer / Runtime Error / Time Limit Exceeded** per test.
- **Error classification** (`learning_services.classify_failure`):
  - compile failure → **Syntax Error**
  - TLE → **Complexity Error**
  - crash or failure on an edge-tagged test → **Edge Case Error**
  - otherwise → **Logic Error**, plus the matching bug explanation.
- Set `JUDGE0_URL` (and `JUDGE0_KEY` for RapidAPI) to run on Judge0 instead.

**Problem bank:** Valid Parentheses, Maximum Subarray, Two Sum, Best Time to Buy and Sell Stock, Contains Duplicate, Climbing Stairs, House Robber. Each has tests tagged `basic / logic / edge`, Java + Python drivers, tutor knowledge and a ThinkMap.

---

## 9. Features page by page

| Page | What you see |
|---|---|
| **Sign-up** | "Your DSA journey. Your rules." Pick a track; the questions change per track; demo presets for 3 students. |
| **Dashboard** | Coach brief, memory alert, track-specific stats (OA readiness / roadmap & mastery / interview countdown & comms), today's plan with a time selector and reasons. |
| **Memory & Catch-up** | Forgetting-curve chart (projected retention if you stop), topic cards (retention, stability, days until blank), Recall buttons, Catch-up Planner. |
| **My Learning Path** | 14-topic roadmap (Arrays → DP) with prerequisites, mastery, weeks, status (mastered / current / needs revision / locked). |
| **Practice Arena** | Problem panel · Monaco editor (Run, Submit, Reset, custom input, autosave, demo code) · Tutor chat + Recall Rescue tab. |
| **ThinkMap** | 10-node React Flow graph (Understand → I/O → Constraints → Brute force → Bottleneck → Data structure → Optimised → Complexity → Edge cases → Validation); progress saved per student. |
| **Smart Revision** | Concept cards + "predict the output" code cards, answered before the reveal; priority queue. |
| **Calendar** | Month grid with the event day starred; click a day for its full plan. |
| **Interview Simulator** | Ananya (animated avatar, voice, typewriter subtitles), typed or spoken answers, live scores, radar-chart report. |
| **Mock OA** | Timed questions, Run sample, one final **Finish & submit**, per-question review, weak topics → roadmap. |
| **Mistake DNA** | 7 categories; each mistake links to problem, evidence, revision card and next problem. |
| **Company Preparation** | Company format and tips, readiness % on its focus topics, personal game plan, ranked problems. |
| **Performance Analytics** | XP over 7 days, mastery, accuracy by topic, mistakes by category, interview scores over time. |
| **Agent Console** | Timeline of every agent run: observed context, decision, model/fallback, latency. |
| **Settings** | Daily minutes, language, **Reset demo**. |

---

## 10. Database design

SQLite via SQLAlchemy (`backend/database/models.py`). The tables are created and migrated automatically on startup.

| Table | Purpose |
|---|---|
| `student_profiles` | Name, track, company, role, deadline, level, language, minutes, weak/revise/familiar topics, XP, streak. |
| `user_preferences` | Today's chosen minutes, editor drafts (autosave), ThinkMap progress, hint levels, time-travel offset. |
| `app_state` | Active profile (server-side, not localStorage). |
| `problems` | Problem catalogue. |
| `user_problem_history` | Every Run/Submit: code, status, passed/total, full result JSON. |
| `user_curriculum` | Roadmap topics: order, prerequisites, mastery, status, weeks. |
| `daily_tasks` | Today's plan items with reasons and done flags. |
| `revision_cards` | Spaced-repetition state per card. |
| `mistake_records` | Classified mistakes with evidence and links. |
| `interview_sessions` | Answers, scores, report. |
| `progress_records` | XP / minutes events (analytics, streak). |
| `topic_memory` | Forgetting-curve state: stability, last review, history. |
| `agent_runs` | Agent traces (observed, decided, source, model, latency). |
| `agent_sessions` | Multi-turn tutor chats and recall ladders. |

---

## 11. API reference

Interactive docs: **http://127.0.0.1:8000/docs**

| Area | Endpoints |
|---|---|
| Profiles | `GET /api/profiles` · `POST /api/profiles` (sign-up) · `POST /api/profiles/active` (switch) · `PUT /api/profiles/active` (settings) · `POST /api/logout` |
| Plan | `GET /api/dashboard` · `GET /api/plan/today` · `POST /api/plan/generate` · `PUT /api/plan/time` · `POST /api/plan/tasks/{id}/done` |
| Calendar | `GET /api/calendar` · `GET /api/calendar/month?year&month` · `GET /api/calendar/day?date` |
| Problems & code | `GET /api/problems` · `GET /api/problems/{slug}` · `PUT /api/drafts/{slug}` · `POST /api/run` · `POST /api/submit` |
| Agents | `POST /api/tutor` · `DELETE /api/tutor/{slug}` · `GET /api/coach` · `POST /api/agents/catchup` · `POST /api/agents/catchup/apply` · `GET /api/agents/status` · `GET /api/agents/runs` |
| Recall | `POST /api/recall/start` · `POST /api/recall/{id}/reply` · `GET /api/recall/active?slug` |
| Memory & time | `GET /api/memory` · `POST /api/time/travel` · `POST /api/time/reset` |
| Revision & mistakes | `GET /api/revisions` · `POST /api/revisions/{id}/answer` · `GET /api/mistakes` · `POST /api/mistakes` |
| Interview | `POST /api/interview/start` · `GET /api/interview` · `POST /api/interview/{id}/answer` · `POST /api/interview/{id}/feedback` |
| Mock OA | `POST /api/mockoa/finish` |
| Other | `GET /api/thinkmap/{slug}` · `PUT /api/thinkmap/{slug}` · `GET /api/curriculum` · `GET /api/company` · `GET /api/analytics` · `POST /api/demo/reset` · `GET /api/health` |

---

## 12. Project structure

```
soch/
├── README.md
├── backend/
│   ├── main.py                       FastAPI app, CORS, startup (DB init + seed)
│   ├── requirements.txt
│   ├── api/routes.py                 all REST endpoints
│   ├── database/
│   │   ├── db.py                     engine, session, auto-migration
│   │   ├── models.py                 13 SQLAlchemy models
│   │   └── seed.py                   3 demo students, reset
│   ├── services/
│   │   ├── agents.py                 Coach, Tutor, Recall Coach, Catch-up Planner, Interviewer
│   │   ├── features.py               Company coach, calendar day plans, Mock OA reviewer
│   │   ├── llm.py                    Ollama client, auto model detection
│   │   ├── memory_model.py           forgetting curve
│   │   ├── clock.py                  per-student virtual clock
│   │   ├── personalization_engine.py time budget, scoring, daily plan, XP/streak
│   │   ├── learning_services.py      revision, mistakes, interview scoring, analytics
│   │   ├── tutor_engine.py           code analysis, bug detectors, offline tutor
│   │   ├── executor.py               javac/java sandbox, Judge0, grading
│   │   ├── problem_bank.py           problems, tests, drivers, demo code
│   │   └── knowledge.py              tutor knowledge, cards, roadmap, ThinkMap, rubrics
│   └── tests/
│       ├── test_demo_flow.py         3-student demo flow
│       ├── test_agents.py            forgetting, recall, catch-up, agents
│       └── fake_ollama.py            stand-in model server for tests
└── frontend/
    ├── package.json · vite.config.ts · index.html
    └── src/
        ├── main.tsx                  routes
        ├── lib/ (api.ts, app.tsx)    API client, active-profile context
        ├── components/               Shell, AgentDock, TodayPlan, CodeEditor, RecallPanel, Interviewer, ui
        └── pages/                    15 pages (Dashboard, Practice, Memory, Calendar, MockOA, Interview …)
```

---

## 13. Setup & run (macOS)

### One-time installs
```bash
brew install python@3.12 node openjdk@21 ollama
echo 'export PATH=/opt/homebrew/opt/openjdk@21/bin:$PATH' >> ~/.zshrc && source ~/.zshrc
javac -version                     # → javac 21.x
ollama pull qwen2.5:3b             # 8 GB Mac  (16 GB+: qwen2.5:7b)
npx n8n                            # optional: automation workflows at http://localhost:5678
```
> `pip install` and `npm install` need internet once. After that everything runs offline.

### Every time — 3 terminal tabs
```bash
# Tab 1 — local AI model
ollama serve

# Tab 2 — backend  (http://127.0.0.1:8000)
cd ~/Downloads/soch/backend
python3.12 -m venv .venv          # first time only
source .venv/bin/activate
pip install -r requirements.txt   # first time only
uvicorn main:app --reload

# Tab 3 — frontend  (http://localhost:5173)
cd ~/Downloads/soch/frontend
npm install                       # first time only
npm run dev
```
Open **http://localhost:5173**. The sidebar should show **● Agents online · qwen2.5:3b**.

### Configuration (optional environment variables)
| Variable | Default | Meaning |
|---|---|---|
| `SOCH_MODEL` | auto-detect | Force a specific Ollama model. |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama address. |
| `SOCH_LLM` | — | `off` = always use offline rules. |
| `N8N_WEBHOOK_URL` | — | n8n webhook for reminders/reports. |
| `JUDGE0_URL`, `JUDGE0_KEY` | — | Use Judge0 instead of the local sandbox. |

### Troubleshooting
| Symptom | Fix |
|---|---|
| "Agents offline" | Start `ollama serve`; check `ollama list` shows a model. |
| `javac not found` | Re-run the `export PATH=…openjdk@21…` line. |
| `cd: string not in pwd` | Folder names with spaces need quotes: `cd "soch 2"`. |
| `Failed to resolve 'pypi.org'` | No internet — reconnect or use a hotspot for the install. |
| Old UI after update | Hard refresh: **Cmd + Shift + R**. |
| Start fresh | Settings → **Reset demo**. |

---

## 14. Demo script

**Before each run:** Settings → Reset demo.

**1 · "I solved DP yesterday, today I'm blank" (Dhanya)**
1. Practice → House Robber → *Demo code → Greedy every-other (buggy)* → **Submit**. It gets Wrong Answer on `[2,1,1,2]` and is recorded as a Logic Error. Ask the tutor *"why is my code failing?"*
2. Paste *DP take/skip* → Submit → Accepted. DP memory is now 100%.
3. Sidebar **+1d**. The dashboard shows *DP 43% — forgotten*, and the plan opens with Recall Rescue.
4. Memory page shows the forgetting curve. Click **Recall House Robber**: the editor clears, you climb the 6-step ladder, then rebuild and Submit. Stability jumps.

**2 · "I skipped DSA for 10 days" (Smrithi)**
1. Solve Valid Parentheses (buggy → Wrong Answer on `(]` → fixed → Accepted).
2. **+10d**. Memory & Catch-up → **Build my catch-up plan** → **Use as today's plan**.

**3 · Mock OA**
Mock OA → Start → write answers → **Finish & submit**. You get a per-question review, and the weak topics are added to the roadmap.

**4 · Interview (Vismaya)**
Interview Simulator → Ananya speaks. Answer by typing or with the 🎤 mic, then view the report.

**5 · Transparency**
Agent Console → expand any run to see what the agent saw and what it decided.

---

## 15. Testing

```bash
cd backend && source .venv/bin/activate
SOCH_LLM=off python tests/test_demo_flow.py     # 5 tests — 3 student flows, isolation, real compile errors
SOCH_LLM=off python tests/test_agents.py        # 3 tests — forgetting, recall, catch-up, agents (offline)

# agent path with a stand-in model server (tests the plumbing, not model quality)
uvicorn tests.fake_ollama:app --port 11555 &
OLLAMA_URL=http://127.0.0.1:11555 SOCH_MODEL=fake python tests/test_agents.py
```
The tests use **real Java compilation**. For example, they assert that the buggy bracket counter really returns `true` for `(]`.

---

## 16. Design decisions & limitations

**Decisions**
- **Local LLM instead of a cloud API:** free, private, works offline, no keys to manage.
- **The LLM explains; code decides.** Verdicts come from the compiler, decay from a formula, budgets from rules. This keeps the system honest and predictable.
- **Every agent has a fallback.** A demo never breaks, and each reply says which mode answered.
- **Server-side state:** profiles, progress and the active user live in SQLite, not localStorage.
- **Transparency first:** the Agent Console exposes each agent's inputs and outputs.

**Limitations**
- Small models (3B) are slower and less precise than cloud models. Answers are good for coaching but can occasionally be shallow.
- The forgetting-curve parameters are illustrative, not fitted to real student data.
- The problem bank is small (7 problems). Adding one means one entry in `problem_bank.py` + `knowledge.py`.
- The local sandbox uses timeouts and memory caps but is not a hardened multi-tenant sandbox. Use Judge0 for untrusted public deployment.
- Company information is representative public patterns, **not** confidential interview questions.
- C++ execution is not wired up (Java and Python are).

---

## 17. Agent orchestration & automation: LangGraph & n8n

> Agents are orchestrated with **LangGraph** on top of the local Ollama model; out-of-app automation runs on **n8n**. Each LangGraph node implements one step of the observe → think → validate → act → trace loop.

### 17.1 LangGraph — agent orchestration

**Why LangGraph:** SOCH's agents are *stateful and multi-step*. The Recall Coach loops on a step until you pass, and the Catch-up Planner validates and retries. LangGraph models this as an explicit graph with typed state, conditional edges, retries and checkpointing, instead of hand-rolled `if/else` and DB session rows.

**Supervisor graph** (one entry point for all agent requests):
```
                    ┌──────────────┐
   request ───────► │  supervisor  │── routes by intent + student state
                    └──────┬───────┘
     ┌──────────┬──────────┼───────────┬──────────────┬──────────────┐
     ▼          ▼          ▼           ▼              ▼              ▼
   Coach      Tutor   Recall Coach  Catch-up      Interviewer    OA Reviewer
                        (subgraph)   Planner
                                    (subgraph)
     └──────────┴──────────┴───────────┴──────────────┴──────────────┘
                                   ▼
                          trace → agent_runs  (Agent Console)
```

**Recall Coach subgraph** (retrieval ladder with loops):
```
 observe_memory ─► ask_step ─► evaluate_answer ──passed──► next_step ──(step 6)──► verify_real_submission ─► update_memory ─► END
                      ▲              │                                                    │ not accepted
                      └── smaller_cue ◄──failed (attempt < 3)                             └──► wait_for_submit
                                     └──failed (attempt ≥ 3) ─► scaffold_hint ─► ask_step
```

**Catch-up Planner subgraph** (plan → validate → repair):
```
 analyse_decay ─► build_candidates ─► llm_plan ─► validate (ids exist, minutes ≤ budget)
                                         ▲              │ invalid (≤ 2 retries)      │ valid
                                         └──── repair ◄─┘                            ▼
                                    rules_fallback ◄── still invalid           apply_to_today ─► END
```

**State (typed):**
```python
class SochState(TypedDict):
    student_id: int
    intent: str                 # tutor | recall | catchup | interview | oa_review | coach
    observed: dict              # profile, memory curve, code, real test results, mistakes
    messages: list              # chat / ladder turns
    step: int                   # recall ladder position
    attempts: int
    decision: dict              # validated output
    source: str                 # llm | fallback
```

**Files:**
```
backend/services/graphs/
├── state.py           SochState
├── supervisor.py      intent routing
├── recall_graph.py    Recall Coach ladder
├── catchup_graph.py   Catch-up Planner
├── tutor_graph.py     Tutor (observe → diagnose → respond)
└── checkpoint.py      SQLite checkpointer (resume sessions after restart)
```

**Dependencies:** `langgraph`, `langchain-ollama`, `langgraph-checkpoint-sqlite`

**Guarantees:** real compiler verdicts, the forgetting-curve formula, rule-based fallbacks, the Agent Console trace and every REST endpoint are independent of the orchestration layer.

### 17.2 n8n — workflow automation

**Why n8n:** some coaching happens *outside* the app, when the student isn't logged in. n8n runs scheduled and event-driven workflows visually, without adding cron jobs to the backend.

**Workflows:**
| Workflow | Trigger | Steps |
|---|---|---|
| **Daily nudge** | Cron, every morning | `GET /api/memory` for each student → if any topic is `forgotten` → send a message: *"DP is at 43% — 5-minute Recall Rescue?"* (Email / Telegram / WhatsApp node) |
| **Weekly report** | Cron, Sunday evening | `GET /api/analytics` → format XP, streak, mastery, mistakes → email summary |
| **Post–Mock OA follow-up** | Webhook from SOCH after `POST /api/mockoa/finish` | Send the score + weak topics → schedule a reminder for the next day's revision |
| **Deadline countdown** | Cron | 3 days / 1 day before OA or interview → send a checklist + link to the Mock OA |
| **Streak saver** | Cron, 9 PM | No activity today → reminder before the streak breaks |

**Integration points:**
```
SOCH backend ──webhook──► n8n  (POST {N8N_WEBHOOK_URL}/soch-events : mock_oa_finished, topic_forgotten, streak_risk)
n8n ──HTTP Request──► SOCH REST API  (/api/memory, /api/analytics, /api/plan/today)
```
- Env var: `N8N_WEBHOOK_URL` (backend sends events only when set).
- Workflow exports stored in `automation/n8n/*.json` (import via n8n → *Import from file*).
- Run n8n locally: `npx n8n` → http://localhost:5678

### 17.3 Full architecture
```
 React UI ──► FastAPI ──► LangGraph supervisor ──► agent subgraphs ──► Ollama (local LLM)
                 │                   │
                 │                   └──► SQLite checkpoints + agent_runs trace
                 ├──► javac/java sandbox (real verdicts)
                 └──webhooks──► n8n ──► Email / Telegram / WhatsApp reminders & reports
```
