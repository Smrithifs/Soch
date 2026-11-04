"""SOCH agents. Each agent:
  1. OBSERVES — gathers the student's real state (profile, memory curve, code, real test results, mistakes, history)
  2. THINKS   — the local LLM reasons over that context (Ollama), with a strict output contract
  3. ACTS     — writes to the plan / memory / mistakes / chat
  4. TRACES   — every run is stored in agent_runs so the UI can show the whole process
If the LLM is offline, the same agent falls back to the deterministic rules and says so.
"""
import json
import time
from datetime import timedelta

from sqlalchemy.orm import Session

from database.models import (AgentRun, AgentSession, DailyTask, MistakeRecord, ProgressRecord, RevisionCard, StudentProfile,
                             UserPreferences, UserProblemHistory)
from . import clock, llm, memory_model as mm, personalization_engine as pe, tutor_engine
from .knowledge import CARDS, KB, TOPIC_CARDS
from .problem_bank import PROBLEMS


# ------------------------------------------------------------------ plumbing
def _trace(db, uid, agent, trigger, observed, decision, source, t0, error=None):
    run = AgentRun(user_id=uid, agent=agent, trigger=trigger[:200], observed=observed, decision=decision, source=source,
                   model=llm.MODEL if source == "llm" else "rules", latency_ms=int((time.time() - t0) * 1000), error=error)
    db.add(run)
    db.flush()
    return run.id


def _student(p: StudentProfile) -> dict:
    return {"name": p.name, "track": pe.TRACK_LABEL[p.track], "level": p.level, "language": p.language, "daily_minutes": p.daily_minutes,
            "company": p.company, "role": p.role, "days_to_event": pe.days_left(p), "goal": p.goal, "starting_topic": p.starting_topic}


def _last_submit(db, uid, slug):
    return db.query(UserProblemHistory).filter_by(user_id=uid, slug=slug, kind="submit").order_by(UserProblemHistory.id.desc()).first()


def _last_accepted(db, uid, slug):
    return db.query(UserProblemHistory).filter_by(user_id=uid, slug=slug, kind="submit", status="Accepted").order_by(UserProblemHistory.id.desc()).first()


def _result_brief(r: dict | None) -> dict | None:
    if not r:
        return None
    ff = r.get("first_failure") or {}
    return {"status": r.get("status"), "passed": r.get("passed"), "total": r.get("total"),
            "first_failing_test": {k: ff.get(k) for k in ("input", "expected", "actual", "stderr")} if ff else None,
            "compiler_error": (r.get("stderr") or "")[:600] if r.get("status") == "Compilation Error" else None}


def _ago(dt) -> str:
    if not dt:
        return "never"
    d = (clock.now() - dt).total_seconds() / 86400
    return f"{d:.1f} days ago" if d >= 1 else f"{d * 24:.0f} hours ago"


# ------------------------------------------------------------------ 1. TUTOR AGENT
TUTOR_SYS = """You are SOCH's DSA tutor — a patient, sharp mentor for an Indian engineering student.
You get the student's profile, how well they currently remember this topic (forgetting-curve retention), the problem,
their CURRENT code, a static analysis of it, and their REAL latest test results from a Java compiler.

Rules:
- Ground every claim in the given context. Quote their actual code / the real failing test. Never invent test results.
- Be Socratic by default: diagnose, then ask ONE guiding question. Don't paste a full solution unless the student explicitly
  asks for the solution/optimal code, or they have already used 3+ hints.
- Complexity questions: analyse THEIR current code, then compare with the optimal.
- Adapt to level ({level}) and to memory: if retention is low, say so kindly and rebuild from the idea, not from code.
- Max ~170 words. Markdown: short paragraphs, `code`, bullet points. No greetings, no filler."""

MODE_ASK = {
    "explain_problem": "Explain this problem simply, with the example, and what makes it tricky.",
    "hint": "Give me the next hint only (don't reveal the solution).",
    "pattern": "Which pattern does this problem use and how could I have recognised it?",
    "failed_approach": "Why is my current approach failing? Use my real test results.",
    "bug": "Find the bug in my current code.",
    "optimal": "Explain the optimal solution and why it works.",
    "edge_cases": "What edge cases should I test for my code?",
    "similar": "Suggest similar problems to practise next and why.",
}


def tutor(db: Session, p: StudentProfile, slug: str, question: str, code: str, language: str, mode: str | None) -> dict:
    t0 = time.time()
    prob, kb = PROBLEMS[slug], KB[slug]
    q = question or MODE_ASK.get(mode or "", "Help me with this problem.")
    sess = db.query(AgentSession).filter_by(user_id=p.id, kind="tutor", slug=slug, status="active").first()
    if not sess:
        sess = AgentSession(user_id=p.id, kind="tutor", slug=slug, messages=[])
        db.add(sess)
        db.flush()
    pref = db.query(UserPreferences).filter_by(user_id=p.id).first()
    hints = (pref.hint_levels or {}).get(slug, 0) if pref else 0
    last = _last_submit(db, p.id, slug)
    a = tutor_engine.analyze_code(code, language)
    ret = {t: (round(100 * r) if (r := mm.topic_retention(db, p.id, t)) is not None else None) for t in prob["topics"]}
    observed = {
        "student": _student(p), "topic_retention_pct": ret, "problem": {"title": prob["title"], "statement": prob["statement"],
        "pattern": prob["pattern"], "optimal_complexity": prob["complexity"], "reference_insight": kb["optimal"]},
        "current_code": code[:4000], "static_analysis": {k: a[k] for k in ("time", "space", "loops", "stack", "hashmap")},
        "known_bug_patterns": tutor_engine.detect_bugs(slug, code, last.result if last else None),
        "latest_real_submission": _result_brief(last.result if last else None), "hints_used": hints,
        "open_mistakes_here": [m.category for m in db.query(MistakeRecord).filter_by(user_id=p.id, slug=slug, status="open")],
    }
    msgs = [{"role": "system", "content": TUTOR_SYS.format(level=p.level)},
            {"role": "user", "content": "CONTEXT (JSON):\n" + json.dumps(observed, default=str)}]
    for m in (sess.messages or [])[-8:]:
        msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": q})
    if pref and (mode == "hint" or (not mode and tutor_engine.classify(q, slug) == "hint")):
        h = dict(pref.hint_levels or {})
        h[slug] = hints + 1
        pref.hint_levels = h
    try:
        body = llm.chat(msgs, temperature=0.35)
        source, title, err, intent = "llm", "Tutor", None, None
    except llm.LLMUnavailable as e:
        r = tutor_engine.respond(slug, question, code, language, last.result if last else None, hints, p.level, mode)
        body, title, source, err = r["body"], r["title"], "fallback", str(e)
        intent = r["intent"]
    sess.messages = list(sess.messages or []) + [{"role": "user", "content": q}, {"role": "assistant", "content": body}]
    run = _trace(db, p.id, "Tutor", q, observed, {"reply": body[:1500]}, source, t0, err)
    db.commit()
    return {"title": title, "body": body, "source": source, "run_id": run, "intent": intent,
            "context": [f"retention {ret}", f"code: {a['time']}/{a['space']}", f"last run: {(last.status if last else 'none')}"]}


# ------------------------------------------------------------------ 2. RECALL RESCUE AGENT
LADDER = [
    ("Cue", "Without looking anything up: in your own words, what does the problem ask for? What goes in, what comes out?"),
    ("Trigger", "What in the problem tells you which pattern to use? (Why this pattern and not, say, greedy or brute force?)"),
    ("State", "Define the core variable(s). If it's DP: what exactly does dp[i] (or your rolling variable) mean?"),
    ("Transition", "How do you get the answer for step i from earlier answers? Write the recurrence / update rule."),
    ("Base & order", "What are the base cases, and in which order do you fill / iterate?"),
    ("Rebuild", "Now write the full solution in the editor from scratch and press Submit. Tell me when it's done (or paste where you're stuck)."),
]

RECALL_SYS = """You are SOCH's Recall Coach. The student solved this problem before but now feels blank — classic forgetting.
Your job is RETRIEVAL PRACTICE, not re-teaching: pull the idea out of THEIR memory with a ladder of cues.

Current ladder step: {step_name} — goal: "{step_goal}"
Rules:
- Evaluate ONLY the student's latest answer against this step's goal (use the reference insight to judge correctness).
- If correct/close: praise briefly and say what they got right (1 line). Set "passed": true.
- If wrong/blank: do NOT give the answer. Give a smaller cue: a tiny example to trace, a question about the last decision,
  or a contrast. Increase help each attempt (attempt #{attempt}). On attempt 3+, give a fill-in-the-blank skeleton. "passed": false.
- Never show their old code. Max 90 words. Warm, direct.
Reply as JSON: {{"reply": "<markdown>", "passed": true|false, "confidence": "low"|"medium"|"high"}}"""


def recall_start(db: Session, p: StudentProfile, slug: str) -> dict:
    t0 = time.time()
    db.query(AgentSession).filter_by(user_id=p.id, kind="recall", status="active").update({"status": "abandoned"})
    prob = PROBLEMS[slug]
    acc = _last_accepted(db, p.id, slug)
    topic = prob["topics"][0]
    r = mm.topic_retention(db, p.id, topic)
    intro = (f"You solved **{prob['title']}** {_ago(acc.created_at) if acc else 'before'}. Your {topic} memory is at "
             f"**{round(100 * r) if r is not None else '?'}%** now — feeling blank is normal; that's the forgetting curve, not a lack of ability.\n\n"
             "We'll pull it back step by step. Answering from memory (even badly) is what makes it stick — reading the solution doesn't.\n\n"
             f"**Step 1 · {LADDER[0][0]}** — {LADDER[0][1]}")
    s = AgentSession(user_id=p.id, kind="recall", slug=slug, stage=0, messages=[{"role": "assistant", "content": intro, "stage": 0}])
    db.add(s)
    db.flush()
    _trace(db, p.id, "Recall Coach", f"start recall on {prob['title']}",
           {"topic": topic, "retention_pct": round(100 * r) if r is not None else None, "last_solved": acc.created_at.isoformat() if acc else None},
           {"ladder": [x[0] for x in LADDER]}, "rules", t0)
    db.commit()
    return recall_view(s)


def recall_view(s: AgentSession) -> dict:
    return {"id": s.id, "slug": s.slug, "stage": s.stage, "steps": [x[0] for x in LADDER], "messages": s.messages, "status": s.status, "outcome": s.outcome}


def recall_reply(db: Session, p: StudentProfile, sid: int, answer: str) -> dict:
    t0 = time.time()
    s = db.query(AgentSession).filter_by(id=sid, user_id=p.id, kind="recall").first()
    if not s or s.status != "active":
        raise KeyError("session")
    prob, kb = PROBLEMS[s.slug], KB[s.slug]
    msgs = list(s.messages or []) + [{"role": "user", "content": answer, "stage": s.stage}]
    attempt = sum(1 for m in msgs if m["role"] == "user" and m.get("stage") == s.stage)
    step_name, step_goal = LADDER[s.stage]
    source, err = "llm", None

    if step_name == "Rebuild":  # judged by the real compiler, not the model
        last = _last_submit(db, p.id, s.slug)
        started = s.created_at
        ok = last and last.status == "Accepted" and last.created_at >= started
        passed = bool(ok)
        reply = (f"✅ Real submission **Accepted** ({last.passed}/{last.total}). You rebuilt it from memory."
                 if ok else f"I don't see an Accepted submission since we started (latest: **{last.status if last else 'none'}**). "
                 f"Submit in the editor first — I only trust the real test run. {('Failing on `' + (last.result.get('first_failure') or {}).get('input', '') + '`.') if last and last.result.get('first_failure') else ''}")
        conf, source = "high" if ok else "low", "rules"
    else:
        ctx = {"problem": prob["title"], "statement": prob["statement"], "reference_insight": {"pattern": kb["pattern"], "optimal": kb["optimal"],
               "hints": kb["hints"]}, "student_answer": answer}
        try:
            out = llm.chat([{"role": "system", "content": RECALL_SYS.format(step_name=step_name, step_goal=step_goal, attempt=attempt)},
                            {"role": "user", "content": json.dumps(ctx)}], want_json=True, temperature=0.3, max_tokens=350)
            reply, passed, conf = str(out.get("reply", "")).strip(), bool(out.get("passed")), out.get("confidence", "medium")
            if not reply:
                raise llm.LLMUnavailable("empty reply")
        except llm.LLMUnavailable as e:
            source, err = "fallback", str(e)
            words = len(answer.split())
            passed = words >= 6 or attempt >= 3
            hint = kb["hints"][min(s.stage // 2, len(kb["hints"]) - 1)]
            reply = ("Good — that's the idea. " if passed else f"Let's make it smaller. {hint}") if attempt < 3 else f"Here's a scaffold to finish the thought: {hint}"
            conf = "medium" if passed else "low"
    msgs.append({"role": "assistant", "content": reply, "stage": s.stage, "passed": passed, "source": source})
    if passed:
        s.stage += 1
        if s.stage < len(LADDER):
            msgs.append({"role": "assistant", "content": f"**Step {s.stage + 1} · {LADDER[s.stage][0]}** — {LADDER[s.stage][1]}", "stage": s.stage})
        else:
            s.status = "complete"
            struggled = sum(1 for m in msgs if m.get("passed") is False)
            s.outcome = "independent" if struggled <= 1 else "assisted"
            quality = "strong" if s.outcome == "independent" else "weak"
            mem = mm.reinforce(db, p.id, prob["topics"][0], quality, source="recall")
            # schedule the next retrieval before it fades again
            for k in TOPIC_CARDS.get(mm.norm(prob["topics"][0]), [])[:2]:
                c = db.query(RevisionCard).filter_by(user_id=p.id, card_key=k).first()
                if c:
                    c.due_at = clock.now() + timedelta(days=1)
            r_now = mm.retention(mem)
            msgs.append({"role": "assistant", "stage": s.stage, "content":
                         f"🎯 Recall complete ({s.outcome}, {struggled} assisted step{'s' if struggled != 1 else ''}). "
                         f"{prob['topics'][0]} stability is now **{mem.stability:.1f} days** (retention {round(100 * r_now)}%). "
                         "I've queued a quick recall card for tomorrow — retrieving it again just before it fades is what makes it permanent."})
            pe.award(db, p, "recall_complete", 30, 10, {"slug": s.slug, "outcome": s.outcome})
    s.messages = msgs
    _trace(db, p.id, "Recall Coach", f"{step_name}: {answer[:120]}", {"step": step_name, "attempt": attempt, "answer": answer[:500]},
           {"passed": passed, "confidence": conf, "reply": reply[:800]}, source, t0, err)
    db.commit()
    return recall_view(s)


# ------------------------------------------------------------------ 3. CATCH-UP PLANNER AGENT
PLANNER_SYS = """You are SOCH's Catch-up Planner. The student was away and has been forgetting. You receive a precise
analysis (forgetting-curve retention per topic, days away, deadline, minutes available today) and a list of CANDIDATE tasks with ids.
Choose and ORDER the tasks for today. Rules:
- Total minutes must be <= minutes_available. Use only candidate ids.
- Rescue topics in the 'forgotten' band first (recall before new problems), then 'fading', then the deadline-critical work.
- If a deadline is <= 3 days away, favour revision and recall over new problems.
- Give each chosen task a one-sentence, specific reason that references the data (retention %, days away, mistakes).
Reply JSON: {"message": "<2-3 sentence note to the student: what happened while away and today's strategy>",
 "tasks": [{"id": "<candidate id>", "reason": "<why>"}]}"""


def _catchup_analysis(db, p) -> tuple[dict, list[dict]]:
    last = db.query(ProgressRecord).filter_by(user_id=p.id).order_by(ProgressRecord.created_at.desc()).first()
    away = round((clock.now() - last.created_at).total_seconds() / 86400, 1) if last else None
    mem = mm.snapshot(db, p.id)
    minutes = pe.available_minutes(db, p)
    cands = []
    solved = {}
    for h in db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit", status="Accepted").order_by(UserProblemHistory.id):
        solved[h.slug] = h
    for m in mem:
        if m["status"] == "strong":
            continue
        for slug, h in solved.items():
            if mm.norm(PROBLEMS[slug]["topics"][0]) == m["topic"]:
                cands.append({"id": f"recall:{slug}", "kind": "recall", "ref": slug, "minutes": 8, "topic": m["topic"],
                              "title": f"Recall Rescue: {PROBLEMS[slug]['title']}", "retention": m["retention"]})
        for k in TOPIC_CARDS.get(m["topic"], [])[:3]:
            cands.append({"id": f"card:{k}", "kind": "revision", "ref": k, "minutes": 1.5, "topic": m["topic"],
                          "title": f"{m['topic']} recall card: {CARDS[k]['concept']}", "retention": m["retention"]})
    for slug, why in pe.select_problems(db, p, 2):
        cands.append({"id": f"problem:{slug}", "kind": "problem", "ref": slug, "minutes": 10, "topic": PROBLEMS[slug]["topics"][0],
                      "title": PROBLEMS[slug]["title"], "why": why})
    analysis = {"student": _student(p), "days_away": away, "minutes_available": minutes, "memory": [
        {k: m[k] for k in ("topic", "retention", "status", "stability_days", "days_since", "forgotten_in_days")} for m in mem],
        "open_mistakes": [m.category + " / " + (m.topic or "") for m in db.query(MistakeRecord).filter_by(user_id=p.id, status="open").limit(6)]}
    return analysis, cands


def catch_up(db: Session, p: StudentProfile) -> dict:
    t0 = time.time()
    analysis, cands = _catchup_analysis(db, p)
    by_id = {c["id"]: c for c in cands}
    source, err = "llm", None
    try:
        out = llm.chat([{"role": "system", "content": PLANNER_SYS},
                        {"role": "user", "content": json.dumps({"analysis": analysis, "candidates": [{k: c[k] for k in c if k != "why"} for c in cands]})}],
                       want_json=True, temperature=0.2, max_tokens=700)
        chosen, total = [], 0.0
        for t in out.get("tasks", []):
            c = by_id.get(str(t.get("id")))
            if c and c not in chosen and total + c["minutes"] <= analysis["minutes_available"] + 0.01:
                chosen.append(c | {"reason": str(t.get("reason", ""))[:300]})
                total += c["minutes"]
        if not chosen:
            raise llm.LLMUnavailable("model chose no valid tasks")
        message = str(out.get("message", ""))
    except llm.LLMUnavailable as e:
        source, err = "fallback", str(e)
        order = {"recall": 0, "revision": 1, "problem": 2}
        chosen, total = [], 0.0
        for c in sorted(cands, key=lambda c: (c.get("retention", 101), order[c["kind"]])):
            if total + c["minutes"] <= analysis["minutes_available"]:
                why = (f"{c['topic']} is at {c['retention']}% retention" if "retention" in c else ", ".join(c.get("why", [])))
                chosen.append(c | {"reason": why + ("; rebuild it from memory before new work." if c["kind"] == "recall" else ".")})
                total += c["minutes"]
        forgotten = [m["topic"] for m in analysis["memory"] if m["status"] == "forgotten"]
        message = (f"You've been away {analysis['days_away'] or 0} days. " + (f"{', '.join(forgotten)} dropped into the forgotten zone, so today starts with recall, not new problems."
                                                                              if forgotten else "Nothing is fully forgotten yet — light revision keeps it that way."))
    plan = {"message": message, "tasks": chosen, "total_minutes": round(total, 1), "analysis": analysis, "source": source}
    plan["run_id"] = _trace(db, p.id, "Catch-up Planner", f"away {analysis['days_away']} days", analysis,
                            {"message": message, "tasks": [c["id"] for c in chosen]}, source, t0, err)
    db.commit()
    return plan


def apply_catch_up(db: Session, p: StudentProfile, tasks: list[dict]) -> dict:
    db.query(DailyTask).filter_by(user_id=p.id, day=pe.today()).delete()
    for i, t in enumerate(tasks):
        db.add(DailyTask(user_id=p.id, day=pe.today(), position=i, kind=t["kind"], ref=t["ref"], title=t["title"], minutes=t["minutes"],
                         reason=t.get("reason", ""), done=False))
    db.commit()
    return pe.get_today(db, p)


# ------------------------------------------------------------------ 4. INTERVIEWER AGENT (grading one answer)
INTERVIEW_SYS = """You are a fair technical interviewer running a practice mock (representative questions, not a real company's).
Grade the candidate's answer for the dimension "{dim}" on the problem "{title}". Reference: {ref}.
Score 0-10 (7 = solid interview answer, 10 = excellent and precise). Be specific about what was missing.
If the answer is good but shallow, add ONE short follow-up probe.
Reply JSON: {{"score": <0-10>, "feedback": "<1-2 sentences>", "follow_up": "<question or empty>"}}"""


def grade_interview_answer(db, p, slug, dimension, question, answer, rubric_score, hit, miss) -> dict | None:
    t0 = time.time()
    kb, prob = KB.get(slug, {}), PROBLEMS[slug]
    ref = f"pattern: {kb.get('pattern')}; optimal: {kb.get('optimal')}; complexity {prob['complexity']}; edge cases: {kb.get('edge_cases', [])[:4]}"
    try:
        out = llm.chat([{"role": "system", "content": INTERVIEW_SYS.format(dim=dimension, title=prob["title"], ref=ref)},
                        {"role": "user", "content": f"Question: {question}\nCandidate answer: {answer}"}], want_json=True, temperature=0.2, max_tokens=250)
        score = max(0.0, min(10.0, float(out.get("score", rubric_score))))
        res = {"score": round(score, 1), "feedback": str(out.get("feedback", "")), "follow_up": str(out.get("follow_up", "") or "")}
        _trace(db, p.id, "Interviewer", f"{dimension}: {answer[:100]}", {"dimension": dimension, "answer": answer[:500], "rubric_keyword_score": rubric_score},
               res, "llm", t0)
        return res
    except (llm.LLMUnavailable, ValueError, TypeError) as e:
        _trace(db, p.id, "Interviewer", f"{dimension}: {answer[:100]}", {"dimension": dimension, "answer": answer[:500]},
               {"score": rubric_score, "hit": hit, "miss": miss}, "fallback", t0, str(e))
        return None


# ------------------------------------------------------------------ 5. COACH (daily brief)
COACH_SYS = """You are SOCH's coach. Write today's brief for the student in 3 short sentences (max 70 words), second person,
specific to the data: what their memory looks like, the single most important thing today, and why. No greetings, no emojis."""


def coach_brief(db: Session, p: StudentProfile, refresh: bool = False) -> dict:
    day = pe.today()
    if not refresh:
        cached = db.query(AgentRun).filter_by(user_id=p.id, agent="Coach").order_by(AgentRun.id.desc()).first()
        if cached and (cached.observed or {}).get("day") == day:
            return {"text": cached.decision["text"], "source": cached.source, "run_id": cached.id}
    t0 = time.time()
    mem = mm.snapshot(db, p.id)
    plan = pe.get_today(db, p)
    obs = {"day": day, "student": _student(p), "memory": [{k: m[k] for k in ("topic", "retention", "status")} for m in mem],
           "today_tasks": [t["title"] for t in plan["tasks"]], "streak": p.streak,
           "open_mistakes": [m.category for m in db.query(MistakeRecord).filter_by(user_id=p.id, status="open").limit(5)]}
    try:
        text, source, err = llm.chat([{"role": "system", "content": COACH_SYS}, {"role": "user", "content": json.dumps(obs)}], temperature=0.5, max_tokens=160), "llm", None
    except llm.LLMUnavailable as e:
        weak = [m for m in mem if m["status"] != "strong"]
        text = (f"{weak[0]['topic']} has dropped to {weak[0]['retention']}% retention — start with a recall before anything new. "
                if weak else "Your memory is in good shape across studied topics. ")
        text += f"Today: {', '.join(obs['today_tasks'][:2]) or 'a light revision'}. "
        text += "Retrieving from memory beats re-reading; struggle a little before taking a hint."
        source, err = "fallback", str(e)
    rid = _trace(db, p.id, "Coach", "daily brief", obs, {"text": text}, source, t0, err)
    db.commit()
    return {"text": text, "source": source, "run_id": rid}
