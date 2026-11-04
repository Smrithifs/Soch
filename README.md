# SOCH: agentic DSA preparation

## The agents
| Agent | What it does | What it sees |
|---|---|---|
| **Coach** | Writes the daily brief on the dashboard | Your memory curve, today's plan, open mistakes |
| **Tutor** | Socratic help in the Practice Arena, keeping the chat in context | Your current code, the real compiler and test results, hints used, retention for the topic |
| **Recall Coach** | Recall Rescue for when you solved it yesterday and can't approach it today. It's a six-step retrieval ladder (Cue, Trigger, State, Transition, Base & order, Rebuild), and the last step only passes after a real Accepted submission | Your answer to the current step, the reference insight, how long you've been away |
| **Catch-up Planner** | After a gap, picks and orders today's work. Recall comes before new problems, and the plan has to fit your minutes and use only real task ids | Retention per topic, days away, deadline, candidate tasks |
| **Interviewer** | Grades each mock-interview answer and asks follow-up probes | Your answer, rubric, reference; code correctness comes from your real submission |

Every run is logged in the **Agent Console**, which shows what each agent observed, what it decided, the model used, and the latency.

## Forgetting and catch-up
Each topic follows a forgetting curve, `R = e^(−t/S)`. After a first solve, S = 1.2 days, so retention is about 43% the next day. That's the "I solved DP yesterday and I'm blank today" effect. A strong recall made just as a topic fades grows S the most, while hints or failures shrink it. Use the **time-travel buttons (+1d / +3d / +10d)** in the sidebar to show this live:
1. Solve House Robber (DP), then press **+1d**. DP drops to 43% (forgotten), the dashboard flags it, and today's plan opens with *Recall Rescue: House Robber*.
2. Do the Recall Rescue. The editor is cleared, you rebuild the solution from memory, and the real submission closes the loop. DP stability jumps, and a review is scheduled for tomorrow.
3. Press **+10d**. Memory & Catch-up shows "away 11 days". The **Catch-up Planner** builds a plan, and you can apply it to today and inspect the decision in the Agent Console.

## Set up the local model (once)
```bash
brew install ollama
ollama serve                 # or open the Ollama app
ollama pull qwen2.5:7b       # ~4.7 GB; on an 8 GB Mac use: ollama pull qwen2.5:3b  and  export SOCH_MODEL=qwen2.5:3b
```
The sidebar shows **Agents online · qwen2.5:7b** when everything is connected. Optional settings: `SOCH_MODEL`, `OLLAMA_URL`, and `SOCH_LLM=off` to force offline rules.

## Requirements (macOS)

| Tool | Version | Install |
|---|---|---|
| Python | 3.10+ | `brew install python` |
| Node | 18+ | `brew install node` |
| **JDK** | 17+ (tested on 21) | `brew install openjdk@21`, then `sudo ln -sfn $(brew --prefix)/opt/openjdk@21/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-21.jdk` |

Check with `javac -version`. Without a JDK, Run and Submit return a clear *503 "javac not found"* error. They never return a fake result.

## Run

```bash
# Terminal 1: backend (http://127.0.0.1:8000)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Terminal 2: frontend (http://localhost:5173)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. On first start the backend creates `backend/soch.db` and seeds **Smrithi**, **Dhanya** and **Vismaya**.

### Optional: Judge0 instead of the local sandbox
```bash
export JUDGE0_URL=https://judge0-ce.p.rapidapi.com   # or your self-hosted http://localhost:2358
export JUDGE0_KEY=<rapidapi key>                        # only for RapidAPI
```

## Tests

```bash
cd backend
SOCH_LLM=off python tests/test_demo_flow.py      # original 3-student demo flow
SOCH_LLM=off python tests/test_agents.py         # forgetting, Recall Rescue, catch-up, agents (offline fallback)
# Agent plumbing against a stand-in Ollama (no real model, just the API shape):
uvicorn tests.fake_ollama:app --port 11555 &
OLLAMA_URL=http://127.0.0.1:11555 SOCH_MODEL=fake python tests/test_agents.py
```
The tests run the full demo flow for all three users through the API, using real Java compilation. They check Wrong Answer on `(]`, Logic Error classification, the tutor answers, the 15/10/5-minute plan rules, the recall miss, the interview report, profile isolation, logout and real compile errors.

## Demo script
1. **Smrithi:** on the sign-up screen choose Online Assessment → Zscaler → 7 days → 2 questions → Beginner/Java → 25 min. The dashboard shows the OA countdown, readiness and a plan of Valid Parentheses, Maximum Subarray and one revision. In Practice Arena, use **Demo code → Paste: Counter approach (buggy)** and Submit: it returns Wrong Answer on `(]` and records a Logic Error. Ask *"why is my code failing?"*, paste the Stack solution and Submit to get Accepted. Then do Maximum Subarray, a revision card and Mistake DNA.
2. **Dhanya:** choose DSA Learning → Hashing → 6 months → 15 min. Solve Two Sum and ask about the HashMap and complexity. Switch the plan between **10m** and **5m** (5m gives revision only). Answer a card wrong in Smart Revision, then open Mistake DNA.
3. **Vismaya:** choose Technical Interviews → Microsoft → SWE Internship → 3 days → Arrays/Hashing/Stacks → 20 min. Look at the dashboard and the three-day plan, solve Best Time to Buy and Sell Stock, ask follow-ups, then run the Interview Simulator through to the feedback report.

The sign-up card has **Demo presets** that fill in each profile. Signing up again with an existing name updates that profile. **Settings → Reset demo** restores the three original profiles.

## Architecture

```
backend/
  main.py                      FastAPI app (lifespan → init_db + seed)
  api/routes.py                all endpoints (validation + transactions only)
  database/db.py, models.py    SQLAlchemy + SQLite (StudentProfile, UserPreferences, Problem, UserProblemHistory,
                               UserCurriculum, DailyTask, RevisionCard, MistakeRecord, InterviewSession, ProgressRecord)
  database/seed.py             demo profiles, reset
  services/personalization_engine.py   track/time/topic/problem/revision rules, daily schedule, mastery, XP/streak, readiness
  services/tutor_engine.py     intent classification, static code analysis, bug detectors, line-by-line explainer
  services/learning_services.py spaced repetition, error classification, Mistake DNA, interview rubric scoring, analytics
  services/executor.py         real execution (local sandbox / Judge0), per-test grading
  services/problem_bank.py     problems, test cases, stdin drivers, demo code presets
  services/knowledge.py        per-problem tutor knowledge, revision cards, roadmap, ThinkMap, interview rubrics
frontend/src/
  pages/  Signup, Dashboard (3 track variants), LearningPath, Practice, ThinkMap, Revision, Calendar,
          Interview, MockOA, MistakeDNA, Company, Analytics, Settings
  components/ Shell (sidebar + profile switcher), TodayPlan (time selector), CodeEditor (Monaco, bundled offline), ui
```

### Key rules (see `personalization_engine.time_budget`)
- Under 8 min: revision only (up to 3 cards).
- 8–19 min: 1 problem (8–9 min) plus revision cards at 2 min each.
- 20 min or more, OA: `min(questions_expected, (min-5)//10)` timed problems plus 1 short revision.
- 20 min or more, Interview ≤ 7 days away: 1 problem, recall cards at 1.5 min, 1 communication drill.
- 20 min or more, Learning: 1 problem (2 if ≥ 35 min) plus prerequisite revision.
- Problem score combines: topic priority (open mistakes, then declared topics, then current topic), company weight, track frequency, a +50 bonus for a previously failed problem (interview track), a −30 penalty if already solved. Ties break alphabetically, so there is no randomness.
- Spaced repetition: a correct answer sets the interval to 1, 3, 7, 14, then 30 days. A wrong answer brings the card back in 10 minutes, records a Concept Recall Error and marks the topic for revision.

## Notes on the existing AlgoPilot code
- The email/password login (`AuthPage`, `/api/auth/*`) is removed because the brief asks for no login-first screen. Profiles are chosen through sign-up and the sidebar switcher. The active profile is stored server-side, not in localStorage.
- `PredefinedResponse` is replaced by the agents (`services/agents.py`). `tutor_engine.py` and `knowledge.py` are now the offline fallback and the reference knowledge the agents use.
- `mcqs.py` randomness is replaced by the deterministic revision-card bank and priority scoring.
- The C++ executor is not wired up. Java and Python have drivers.
