# SOCH — Agentic DSA Preparation Platform

**Think smarter. Practice strategically. Remember what you learn.**

SOCH is an intelligent, multi-agent DSA preparation platform designed to make coding interview preparation more personalized, adaptive, and effective.

Instead of giving every student the same problem list, SOCH understands individual learning goals, tracks problem-solving behavior, identifies knowledge gaps, and continuously adapts the preparation strategy.

Whether a student is learning Data Structures and Algorithms from scratch, preparing for an Online Assessment, or approaching a technical interview, SOCH creates a learning experience around their goals, available time, performance, and retention.

---

## ✨ What makes SOCH different?

Most coding platforms focus on what problem a student should solve.

SOCH focuses on something more important:

**What should this student learn next, why are they struggling, what have they forgotten, and how should their preparation adapt?**

SOCH brings together:

- **Multi-agent intelligence:** Specialized agents collaborate to manage different aspects of a student's preparation.
- **Personalized learning:** Learning paths adapt to the student's goals, proficiency, deadlines, and daily availability.
- **Adaptive memory:** A forgetting-curve model identifies when previously learned concepts need reinforcement.
- **Socratic tutoring:** Students receive contextual guidance based on their actual code and execution results.
- **Intelligent catch-up:** Missed study days trigger a redesigned plan that prioritizes forgotten concepts.
- **Real code evaluation:** Java and Python submissions are compiled and executed against actual test cases.
- **Interview readiness:** Mock interviews evaluate problem-solving, technical reasoning, and communication.

---

## 🤖 Meet the five specialized agents

SOCH uses a multi-agent architecture in which each agent has a clearly defined responsibility. LangGraph coordinates the agent workflow, while n8n supports workflow automation and integrations.

| Agent | Responsibility | What it observes |
|---|---|---|
| **Coach Agent** | Generates personalized daily preparation briefs and recommends what to focus on. | Memory retention, daily goals, open mistakes, and pending tasks. |
| **Tutor Agent** | Provides contextual, Socratic guidance inside the Practice Arena. | Current code, compiler output, test results, hints used, and topic retention. |
| **Recall Coach Agent** | Helps students reconstruct previously learned solutions through a six-step retrieval process. | Current answer, reference insights, and time since last practice. |
| **Catch-up Planner Agent** | Reorganizes learning after a break, prioritizing revision before introducing new concepts. | Topics due for revision, days away, deadlines, available time, and candidate tasks. |
| **Interviewer Agent** | Conducts mock interviews, evaluates responses, and asks relevant follow-up questions. | Student responses, evaluation rubrics, reference solutions, and submission correctness. |

### Agent collaboration

The agents operate as specialized components within a coordinated workflow rather than independent chatbots.

The platform follows an adaptive cycle:

**Observe → Reason → Retrieve → Plan → Act → Evaluate → Adapt**

Every agent execution is recorded in the Agent Console, providing visibility into the agent's observations, decisions, selected model, and execution latency.

---

## 🧠 The science of remembering DSA

One of SOCH's central features is its adaptive memory system.

Learning a problem once does not guarantee that a student can solve it again independently.

SOCH models topic retention using the forgetting curve:

\[
R=e^{-t/S}
\]

Where:

- \(R\) = estimated retention.
- \(t\) = time elapsed since learning.
- \(S\) = memory stability.

After a first successful solve, SOCH initializes memory stability to 1.2 days.

This means estimated retention after one day is approximately 43%.

Rather than waiting for a student to forget an entire concept, SOCH identifies when reinforcement is needed and schedules a targeted revision.

### Recall Rescue: Six-step retrieval ladder

When a student cannot remember a previously solved problem, Recall Coach guides them through six stages:

1. **Cue:** Recognize the problem's important clues.
2. **Trigger:** Identify the underlying pattern or technique.
3. **State:** Determine what information needs to be maintained.
4. **Transition:** Explain how the state changes.
5. **Base & Order:** Identify base cases and the order of computation.
6. **Rebuild:** Reconstruct the solution independently.

The final stage is completed only after a real Accepted submission.

A successful recall strengthens topic stability and schedules the next review.

### Time-travel simulation

SOCH includes interactive time-travel controls:

- **+1 day:** Simulate forgetting after one day.
- **+3 days:** Observe how retention changes.
- **+10 days:** Simulate a longer study gap.

Students can observe how memory changes, how the dashboard identifies revision needs, and how the Catch-up Planner reorganizes their preparation.

---

## 📚 Personalized learning experiences

SOCH supports three distinct preparation tracks.

### 1. Online Assessment Preparation

Designed for students preparing for company-specific coding assessments.

Students can configure:
- Target company.
- Assessment deadline.
- Expected number of questions.
- Current proficiency.
- Preferred programming language.
- Daily preparation time.

SOCH prioritizes relevant problems, revisions, and timed practice based on the assessment timeline.

### 2. DSA Learning

Designed for students building their DSA foundations.

The platform organizes learning around:
- Topic prerequisites.
- Problem-solving patterns.
- Conceptual understanding.
- Progressive practice.
- Spaced revision.

Students can learn at their own pace while SOCH adapts daily tasks to their available time.

### 3. Technical Interview Preparation

Designed for students approaching technical interviews.

The preparation experience includes:
- Topic-focused problem solving.
- Interview-style explanations.
- Complexity analysis.
- Communication drills.
- Mock interviews.
- Personalized feedback reports.

---

## 💻 Practice Arena

The Practice Arena combines coding, evaluation, and intelligent tutoring in one environment.

Students can:

- Write and edit code using Monaco Editor.
- Practice problems in Java and Python.
- Run code against test cases.
- Submit solutions for actual evaluation.
- Receive compiler errors and Wrong Answer results.
- Ask the Tutor Agent questions about their implementation.
- Rebuild incorrect solutions with contextual guidance.

SOCH distinguishes between different types of mistakes, including:

- Conceptual errors.
- Logic errors.
- Implementation errors.
- Complexity issues.
- Edge-case failures.
- Communication and explanation gaps.

Code correctness is determined through actual execution, not simply by asking a language model whether a solution looks correct.

---

## 🗺️ ThinkMap 2.0

ThinkMap helps students understand how to approach a DSA problem instead of immediately jumping to the final code.

It organizes problem-solving into five stages:

1. **Understand:** Identify the problem requirements.
2. **Find Key Ideas:** Recognize relevant patterns and observations.
3. **Choose Approach:** Select a suitable algorithm.
4. **Analyze Complexity:** Evaluate time and space complexity.
5. **Optimized Solution:** Develop and understand the final implementation.

The objective is to develop independent problem-solving ability rather than dependency on generated solutions.

---

## 🔄 Smart Revision and Mistake DNA

### Smart Revision

SOCH uses spaced repetition to reinforce concepts at progressively increasing intervals.

A successful recall advances the revision schedule:

**1 → 3 → 7 → 14 → 30 days**

An incorrect response brings the revision card back after 10 minutes, records a Concept Recall Error, and flags the topic for additional practice.

### Mistake DNA

Mistake DNA identifies recurring weaknesses in a student's problem-solving behavior.

Instead of simply displaying the number of incorrect submissions, SOCH categorizes mistakes to help students understand why they are struggling.

The resulting insights can influence future revision and problem recommendations.

---

## 🏗️ System Architecture

SOCH combines a modern web application, specialized agents, model inference, code execution, and persistent learning data.

### Technology stack

| Layer | Technologies | Purpose |
|---|---|---|
| Frontend | React, Vite | Interactive student dashboard and learning interface. |
| Code Editor | Monaco Editor | Coding and submission experience. |
| Visual Learning | React Flow | Interactive ThinkMap visualizations. |
| Backend | Python, FastAPI | API endpoints and application services. |
| Agent Orchestration | LangGraph | Coordinates agent workflows, state, and conditional decisions. |
| Workflow Automation | n8n | Automates scheduled tasks, notifications, and service integrations. |
| Language Model | Qwen 2.5 via Ollama | Local language-model inference for contextual assistance. |
| Knowledge Retrieval | RAG | Retrieves relevant DSA knowledge to ground model responses. |
| Database | SQLite, SQLAlchemy | Stores student profiles, progress, tasks, and learning history. |
| Code Execution | Local sandbox / optional Judge0 | Compiles and evaluates code against test cases. |

### How the system works

1. A student enters their preparation goals, proficiency, language, deadline, and available study time.
2. The backend retrieves the student's profile, progress, and learning history.
3. The personalization engine identifies priorities and creates a time-aware learning plan.
4. LangGraph coordinates the appropriate agent workflow.
5. Agents use relevant student context, reference knowledge, and available tools to make decisions.
6. The Tutor Agent can use Qwen 2.5 through Ollama for contextual explanations and guidance.
7. Submitted code is compiled and executed through the code execution service.
8. Results are recorded and used to update progress, mistakes, and revision schedules.
9. The Coach and Catch-up Planner use the updated learning state to guide the next session.

**Important architectural distinction:** LangGraph coordinates agent reasoning and workflow state; n8n handles automation and external workflow integrations. They serve complementary purposes.

---

## 🖥️ Local Model Setup

SOCH supports local inference through Ollama, allowing the platform to use a locally hosted language model without requiring a cloud AI API key for model inference.

Install Ollama:

```bash
brew install ollama
```

Start the Ollama service:

```bash
ollama serve
```

Download the recommended model:

```bash
ollama pull qwen2.5:7b
```

For an 8 GB Mac, use the smaller model:

```bash
ollama pull qwen2.5:3b
```

Configure the model:

```bash
export SOCH_MODEL=qwen2.5:3b
```

Optional configuration:

```bash
export OLLAMA_URL=http://localhost:11434
export SOCH_LLM=off
```

Setting `SOCH_LLM=off` disables language-model inference and uses the platform's offline fallback behavior.

---

## 🧩 Project Structure

```text
SOCH/
│
├── backend/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   ├── models.py
│   │   └── seed.py
│   │
│   ├── services/
│   │   ├── agents.py
│   │   ├── personalization_engine.py
│   │   ├── tutor_engine.py
│   │   ├── learning_services.py
│   │   ├── executor.py
│   │   ├── problem_bank.py
│   │   └── knowledge.py
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── ...
│   └── package.json
│
└── README.md
```

### Core backend services

- **Personalization Engine:** Calculates topic priorities, daily schedules, readiness, and learning progress.
- **Agent Services:** Implements specialized agent responsibilities and coordinated decision-making.
- **Tutor Engine:** Provides offline tutoring support, code analysis, and fallback explanations.
- **Learning Services:** Handles spaced repetition, error classification, Mistake DNA, and interview evaluation.
- **Execution Service:** Compiles and evaluates student submissions.
- **Knowledge Service:** Provides problem-specific reference material, revision cards, roadmaps, ThinkMap content, and interview rubrics.

---

## 🚀 Getting Started

### Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| JDK | 17+ |
| Ollama | Latest compatible version |

Install the JDK on macOS:

```bash
brew install openjdk@21

sudo ln -sfn \
$(brew --prefix)/opt/openjdk@21/libexec/openjdk.jdk \
/Library/Java/JavaVirtualMachines/openjdk-21.jdk
```

Verify:

```bash
javac -version
```

### Start the backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

### Start the frontend

Open a second terminal:

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

Open the frontend in your browser.

On the first backend startup, SOCH initializes its local database and loads three demonstration student profiles.

---

## 🧪 Testing and Reliability

SOCH emphasizes real execution and verifiable learning outcomes.

Run the demonstration-flow tests:

```bash
cd backend

SOCH_LLM=off python tests/test_demo_flow.py
```

Run agent and learning-system tests:

```bash
SOCH_LLM=off python tests/test_agents.py
```

Test the agent integration against a local stand-in Ollama service:

```bash
uvicorn tests.fake_ollama:app --port 11555 &
```

In another terminal:

```bash
OLLAMA_URL=http://127.0.0.1:11555 \
SOCH_MODEL=fake \
python tests/test_agents.py
```

The test suite covers:

- The three demonstration student journeys.
- Real Java compilation and execution.
- Incorrect bracket validation, including `(]`.
- Logic-error classification.
- Tutor responses.
- Daily time-budget rules.
- Recall Rescue and failed retrieval.
- Interview feedback.
- Student profile isolation.
- Logout behavior.
- Compiler errors.

### Execution reliability

SOCH does not treat an unavailable compiler as a successful submission.

If Java compilation is unavailable, the platform returns a clear service error rather than displaying a fabricated Accepted result.

An optional Judge0 integration can be configured:

```bash
export JUDGE0_URL=https://judge0-ce.p.rapidapi.com
export JUDGE0_KEY=<your-rapidapi-key>
```

For a self-hosted Judge0 instance:

```bash
export JUDGE0_URL=http://localhost:2358
```

---

## 🎯 Demonstration Scenarios

SOCH includes three demonstration journeys representing different student goals.

### Student 1: Online Assessment — Smrithi

**Goal:** Prepare for the Zscaler Online Assessment in seven days.

- Beginner-level DSA.
- Java programming.
- 25 minutes per day.
- Focus on Valid Parentheses and Maximum Subarray.

The demonstration shows how SOCH detects a faulty bracket-validation implementation, identifies a logic error, guides the student toward a stack-based approach, and updates the learning record after an Accepted submission.

### Student 2: DSA Learning — Dhanya

**Goal:** Build DSA fundamentals over six months.

- Beginner-level DSA.
- Java programming.
- 15 minutes per day.
- Focus on Arrays and Hashing.

The demonstration explores Two Sum, HashMap reasoning, complexity analysis, revision scheduling, and adaptation to shorter study sessions.

### Student 3: Technical Interview — Vismaya

**Goal:** Prepare for a Microsoft SWE Internship interview in three days.

- Beginner-level DSA.
- Java programming.
- 20 minutes per day.
- Focus on Arrays, Hashing, and Stacks.

The demonstration covers interview-oriented preparation, Best Time to Buy and Sell Stock, contextual follow-up questions, and a mock-interview feedback report.

Demo presets are available on the sign-up screen. Existing demonstration profiles can be updated by signing up with the same name.

To restore the original demonstration profiles:

**Settings → Reset Demo**

---

## 🔐 Responsible AI and Reliability

SOCH is designed to make its learning decisions observable and its evaluation results verifiable.

Key safeguards include:

- **Execution-based evaluation:** Code correctness is determined through actual compilation and test execution.
- **Transparent agent decisions:** Agent Console records observations, decisions, models, and latency.
- **Offline fallback:** Learning functionality can continue using the platform's offline services when model inference is unavailable.
- **Student-specific data:** Learning histories and profiles are maintained separately.
- **Human control:** Students can review and adjust their learning plans rather than being forced to follow every recommendation.
- **Error awareness:** Compiler failures and unavailable services are reported rather than represented as successful outcomes.

## 🌍 Impact — Making Every Learning Session Count

SOCH aims to address a fundamental problem in technical education: students spend hours practicing DSA, yet often struggle to retain concepts, identify their weaknesses, and prepare effectively for real-world coding assessments and interviews.

By combining personalized learning, agentic assistance, and adaptive memory, SOCH aims to make preparation more focused, measurable, and accessible.

### Impact on Students

- **Reduced learning gaps:** Identifies conceptual and implementation weaknesses instead of treating every incorrect submission as the same mistake.
- **Better knowledge retention:** Uses forgetting-curve-based revision and active recall to help students revisit concepts before they are completely forgotten.
- **Personalized preparation:** Adapts learning plans to individual proficiency, career goals, deadlines, and daily availability.
- **More effective practice:** Helps students understand why their solutions fail instead of simply revealing the correct answer.
- **Improved interview readiness:** Encourages students to explain their reasoning, analyze complexity, and communicate solutions confidently.
- **Accessible learning support:** Provides locally hosted language-model assistance, reducing dependence on cloud AI services when local inference is available.

### Broader Educational Impact

| Challenge | SOCH's contribution |
|---|---|
| One-size-fits-all learning | Individualized learning paths |
| Repeatedly forgetting concepts | Adaptive spaced repetition |
| Difficulty identifying weaknesses | Mistake DNA and error classification |
| Lack of personalized guidance | Specialized learning agents |
| Inefficient preparation after breaks | Intelligent catch-up planning |
| Limited interview practice | Interview simulations and feedback |
| Unclear progress | Learning analytics and readiness tracking |

### Long-Term Vision

SOCH aims to make high-quality, personalized DSA preparation accessible beyond students who can afford individual mentorship or expensive coaching programs.

Our vision is to help colleges, coding clubs, and independent learners build a stronger problem-solving culture through continuous feedback, adaptive learning, and measurable progress.

**From solving more problems to becoming better problem solvers — SOCH makes learning more intentional.**

### How We Measure Impact

We intend to evaluate SOCH through measurable outcomes:

1. Improvement in independent problem-solving accuracy.
2. Retention of previously learned concepts after 1, 3, 7, and 14 days.
3. Reduction in repeated mistakes across practice sessions.
4. Completion of personalized daily learning plans.
5. Improvement in mock-interview evaluation scores.
6. Student engagement, revision consistency, and retention.

*These are proposed evaluation metrics. Their actual improvement will be established through student pilots and performance data.*
---

## 🌱 Our Vision

We believe DSA preparation should be more than solving hundreds of problems.

Students should understand patterns, recognize their weaknesses, retain what they learn, and develop the confidence to solve unfamiliar problems independently.

SOCH aims to transform preparation from a static checklist into a continuous learning process — one that observes, understands, adapts, and grows with every student.

**SOCH — Don't just solve problems. Learn how to think.**

---

*Built with a focus on personalized learning, agentic workflows, and measurable improvement in problem-solving ability.*
