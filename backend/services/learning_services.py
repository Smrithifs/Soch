"""Revision (spaced repetition), mistake classification, interview simulation and analytics."""
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from database.models import (InterviewSession, MistakeRecord, ProgressRecord, RevisionCard, StudentProfile, UserCurriculum,
                             UserPreferences, UserProblemHistory)
from . import memory_model as mm
from . import personalization_engine as pe
from .knowledge import CARDS, interview_steps
from .problem_bank import PROBLEMS
from .tutor_engine import analyze_code, detect_bugs
from . import clock

INTERVALS = [1, 3, 7, 14, 30]  # days after 1st, 2nd, 3rd… consecutive correct answer
DNA_GROUPS = {
    "Concept Recall Error": "conceptual", "Conceptual Misunderstanding": "conceptual", "Pattern Recognition": "pattern",
    "Logic Error": "logic", "Syntax Error": "implementation", "Runtime Error": "implementation", "Implementation Error": "implementation",
    "Complexity Error": "complexity", "Edge Case Error": "edge", "Communication Issue": "communication",
}
PROBLEM_CARD = {"valid-parentheses": "stack_parens", "maximum-subarray": "kadane_reset", "two-sum": "hashmap_store",
                "best-time-to-buy-and-sell-stock": "stock_min", "contains-duplicate": "hashmap_lookup",
                "climbing-stairs": "dp_recurrence", "house-robber": "dp_state"}


# ------------------------------------------------------------------ revision
def card_view(c: RevisionCard, reveal=False) -> dict:
    d = CARDS[c.card_key]
    v = {"id": c.id, "key": c.card_key, "topic": c.topic, "concept": c.concept, "question": d["q"], "options": d["options"],
         "type": d.get("type", "mcq"), "code": d.get("code"),
         "interval_days": c.interval_days, "streak": c.correct_streak, "attempts": c.attempts, "correct": c.correct,
         "due_at": c.due_at.isoformat() if c.due_at else None, "due": (c.due_at or clock.now()) <= clock.now(), "last_result": c.last_result}
    if reveal:
        v |= {"answer": d["correct"], "explanation": d["explain"]}
    return v


def list_revisions(db: Session, p: StudentProfile) -> list[dict]:
    pe.ensure_cards(db, p)
    db.commit()
    cards = db.query(RevisionCard).filter_by(user_id=p.id).all()
    ranked = sorted(cards, key=lambda c: -pe.card_priority(db, p, c)[0])
    return [card_view(c) | {"priority_reasons": pe.card_priority(db, p, c)[1]} for c in ranked]


def answer_card(db: Session, p: StudentProfile, card_id: int, choice: int | None, revealed: bool) -> dict:
    c = db.query(RevisionCard).filter_by(id=card_id, user_id=p.id).first()
    if not c:
        raise KeyError("card")
    d = CARDS[c.card_key]
    correct = (choice == d["correct"]) and not revealed
    c.attempts += 1
    c.last_reviewed = clock.now()
    mistake = None
    if correct:
        c.correct += 1
        c.correct_streak += 1
        c.interval_days = INTERVALS[min(c.correct_streak - 1, len(INTERVALS) - 1)]
        c.due_at = clock.now() + timedelta(days=c.interval_days)
        c.last_result = "right"
        pe.update_topic_mastery(db, p.id, [c.topic], +0.05)
        mm.reinforce(db, p.id, c.topic, "strong", source=f"card:{c.card_key}")
        pe.award(db, p, "revision_correct", 10, 1.5, {"card": c.card_key})
        for m in db.query(MistakeRecord).filter_by(user_id=p.id, revision_card=c.card_key, status="open").all():
            m.status = "improving"
    else:
        c.correct_streak = 0
        c.interval_days = 0
        c.due_at = clock.now() + timedelta(minutes=10)  # earlier revision
        c.last_result = "wrong"
        if mm.topic_retention(db, p.id, c.topic) is not None:
            mm.reinforce(db, p.id, c.topic, "fail", source=f"card:{c.card_key}")
        pe.award(db, p, "revision_wrong", 2, 1.5, {"card": c.card_key})
        chosen = d["options"][choice] if choice is not None and 0 <= choice < len(d["options"]) else "(revealed without answering)"
        mistake = record_mistake(db, p, "Concept Recall Error", slug=_slug_for_topic(c.topic), topic=c.topic,
                                 title=f"Recall miss: {c.concept}",
                                 explanation=f"Asked “{d['q']}” — answered **{chosen}**, correct is **{d['options'][d['correct']]}**. {d['explain']}",
                                 evidence={"card": c.card_key, "chosen": chosen}, card=c.card_key, source="revision")
        cur = db.query(UserCurriculum).filter_by(user_id=p.id, topic=pe.norm_topic(c.topic)).first()
        if cur and cur.status == "done":
            cur.status = "revise"
    pe.mark_task(db, p.id, "revision", c.card_key)
    db.commit()
    return {"correct": correct, "card": card_view(c, reveal=True), "next_due_in": "10 minutes" if not correct else f"{c.interval_days:g} days",
            "mistake_id": mistake.id if mistake else None}


def _slug_for_topic(topic: str) -> str:
    return {"Hashing": "two-sum", "Stacks": "valid-parentheses", "Stacks and Queues": "valid-parentheses", "Arrays": "best-time-to-buy-and-sell-stock",
            "Time Complexity": "two-sum", "Dynamic Programming": "house-robber"}.get(topic, "two-sum")


# ------------------------------------------------------------------ mistakes
def record_mistake(db, p, category, slug, topic, title, explanation, evidence, card=None, source="execution", status="open"):
    existing = db.query(MistakeRecord).filter_by(user_id=p.id, category=category, slug=slug, title=title).first()
    if existing:
        existing.evidence = evidence
        existing.status = "open" if status == "open" else existing.status
        m = existing
    else:
        m = MistakeRecord(user_id=p.id, category=category, dna_group=DNA_GROUPS.get(category, "logic"), slug=slug, topic=topic, title=title,
                          explanation=explanation, evidence=evidence, revision_card=card or PROBLEM_CARD.get(slug),
                          next_problem=PROBLEMS[slug]["next_problem"] if slug in PROBLEMS else None, source=source, status=status)
        db.add(m)
    db.flush()
    if status == "open":
        pe.adjust_after_mistake(db, p, m)
    return m


def classify_failure(slug: str, code: str, result: dict) -> tuple[str, str] | None:
    """Deterministic error classification from a real execution result."""
    st = result["status"]
    if st == "Accepted":
        return None
    if st == "Compilation Error":
        return "Syntax Error", "The code does not compile. Read the first compiler error: it names the line and the missing/unexpected token."
    if st == "Time Limit Exceeded":
        a = analyze_code(code)
        return "Complexity Error", f"Execution exceeded the time limit. Static analysis: {a['time']} ({a['why_time']}); the target is {PROBLEMS[slug]['complexity']['time']}."
    ff = result.get("first_failure") or {}
    if st == "Runtime Error":
        if ff.get("tag") == "edge":
            return "Edge Case Error", f"The program crashed on edge input `{ff.get('input')}`: {(ff.get('stderr') or '').splitlines()[0] if ff.get('stderr') else ''}"
        return "Runtime Error", (ff.get("stderr") or "").splitlines()[0] if ff.get("stderr") else "The program exited with an error."
    bugs = detect_bugs(slug, code, None)
    if ff.get("tag") == "edge" and not any("Logic error" in b for b in bugs):
        return "Edge Case Error", f"Fails on edge input `{ff['input']}` (expected `{ff['expected']}`, got `{ff['actual']}`). " + (bugs[0] if bugs else "")
    return "Logic Error", (bugs[0] if bugs else f"Output differs on `{ff.get('input')}`: expected `{ff.get('expected')}`, got `{ff.get('actual')}`.")


def mistakes_view(db, p) -> dict:
    ms = db.query(MistakeRecord).filter_by(user_id=p.id).order_by(MistakeRecord.id.desc()).all()
    groups = ["conceptual", "pattern", "logic", "implementation", "complexity", "edge", "communication"]
    out = []
    for m in ms:
        out.append({"id": m.id, "category": m.category, "group": m.dna_group, "slug": m.slug, "problem": PROBLEMS.get(m.slug, {}).get("title"),
                    "topic": m.topic, "title": m.title, "explanation": m.explanation, "evidence": m.evidence, "status": m.status, "source": m.source,
                    "revision_card": m.revision_card, "revision_concept": CARDS.get(m.revision_card or "", {}).get("concept"),
                    "next_problem": m.next_problem, "next_problem_title": PROBLEMS.get(m.next_problem or "", {}).get("title"),
                    "created_at": m.created_at.isoformat()})
    return {"groups": {g: sum(1 for m in ms if m.dna_group == g) for g in groups}, "mistakes": out}


# ------------------------------------------------------------------ submissions
def record_submission(db, p, slug, language, code, kind, result) -> dict:
    pref = db.query(UserPreferences).filter_by(user_id=p.id).first()
    hints = (pref.hint_levels or {}).get(slug, 0) if pref else 0
    first_accept = kind == "submit" and result["status"] == "Accepted" and not db.query(UserProblemHistory).filter_by(
        user_id=p.id, slug=slug, kind="submit", status="Accepted").first()
    db.add(UserProblemHistory(user_id=p.id, slug=slug, kind=kind, language=language, code=code, status=result["status"],
                              passed=result.get("passed", 0), total=result.get("total", 0), result=result, hints_used=hints))
    analysis = None
    if kind == "submit":
        cls = classify_failure(slug, code, result)
        pr = PROBLEMS[slug]
        if cls:
            cat, expl = cls
            ff = result.get("first_failure") or {}
            m = record_mistake(db, p, cat, slug, pr["topics"][0], f"{pr['title']}: {cat} on {ff.get('input', 'compile')!r}"[:200], expl,
                               {"input": ff.get("input"), "expected": ff.get("expected"), "actual": ff.get("actual"), "status": result["status"],
                                "passed": result.get("passed"), "total": result.get("total")})
            pe.update_topic_mastery(db, p.id, pr["topics"], -0.05)
            if db.query(UserProblemHistory).filter_by(user_id=p.id, slug=slug, kind="submit", status="Accepted").first():
                mm.reinforce(db, p.id, pr["topics"][0], "fail", source=f"submit:{slug}")  # could solve it before, can't now = lapse
            pe.award(db, p, "submit_failed", 0, 0, {"slug": slug})
            analysis = {"category": cat, "explanation": expl, "mistake_id": m.id}
        else:
            for m in db.query(MistakeRecord).filter_by(user_id=p.id, slug=slug, status="open").all():
                if m.dna_group in ("logic", "implementation", "edge", "complexity"):
                    m.status = "resolved"
            mm.reinforce(db, p.id, pr["topics"][0], "strong" if hints == 0 else "weak", source=f"submit:{slug}")
            if first_accept:
                xp = {"Easy": 50, "Medium": 80}.get(pr["difficulty"], 50) - 5 * hints
                pe.update_topic_mastery(db, p.id, pr["topics"], 0.25)
                pe.award(db, p, "solved", max(20, xp), pe.time_budget(p, pe.available_minutes(db, p))["problem_min"], {"slug": slug, "hints": hints})
            pe.mark_task(db, p.id, "problem", slug)
            # next topic unlocking for learners
            for row in db.query(UserCurriculum).filter_by(user_id=p.id, status="locked").all():
                pre = db.query(UserCurriculum).filter(UserCurriculum.user_id == p.id, UserCurriculum.topic.in_(row.prerequisites or [])).all()
                if pre and all(x.mastery >= 0.5 for x in pre):
                    row.status = "available"
    db.commit()
    return {"analysis": analysis, "xp": p.xp, "streak": p.streak}


# ------------------------------------------------------------------ interview
def start_interview(db, p, slug=None) -> dict:
    # Rule: simulate on today's planned problem (the one just practised); otherwise the top-ranked problem.
    planned = [t["ref"] for t in pe.get_today(db, p)["tasks"] if t["kind"] == "problem"]
    slug = slug or (planned[0] if planned else (pe.select_problems(db, p, 1) or [("two-sum", [])])[0][0])
    db.query(InterviewSession).filter_by(user_id=p.id, status="active").update({"status": "abandoned"})
    s = InterviewSession(user_id=p.id, slug=slug, step=0, answers=[], scores={})
    db.add(s)
    db.commit()
    return interview_state(s)


def interview_state(s: InterviewSession) -> dict:
    steps = interview_steps(s.slug, PROBLEMS[s.slug])
    cur = steps[s.step] if s.step < len(steps) else None
    return {"id": s.id, "slug": s.slug, "title": PROBLEMS[s.slug]["title"], "step": s.step, "total": len(steps), "status": s.status,
            "question": cur["q"] if cur else None, "dimension": cur["dimension"] if cur else None, "answers": s.answers or [],
            "report": s.report, "disclaimer": "Representative practice questions — not actual or confidential company questions."}


def _score_answer(step: dict, text: str) -> tuple[float, list[str], list[str]]:
    t = text.lower().replace("²", "^2")
    groups = step["groups"]
    if not groups:
        return 0, [], []
    hit, miss = [], []
    for g in groups:
        (hit if any(k.lower().replace("²", "^2") in t for k in g) else miss).append(g[0])
    score = 10 * len(hit) / len(groups)
    words = len(re.findall(r"\w+", text))
    if words < 4:
        score = min(score, 3)
    return round(score, 1), hit, miss


def answer_interview(db, p, sid: int, text: str) -> dict:
    s = db.query(InterviewSession).filter_by(id=sid, user_id=p.id).first()
    if not s or s.status != "active":
        raise KeyError("session")
    steps = interview_steps(s.slug, PROBLEMS[s.slug])
    step = steps[s.step]
    graded = "rubric"
    if step["dimension"] == "Code correctness":
        graded = "compiler"
        last = db.query(UserProblemHistory).filter_by(user_id=p.id, slug=s.slug, kind="submit").order_by(UserProblemHistory.id.desc()).first()
        if last:
            score = round(10 * last.passed / max(1, last.total), 1)
            fb = f"Read your latest real submission: **{last.status}** ({last.passed}/{last.total} tests)."
        else:
            score, fb = 0, "No submission found for this problem — code correctness can't be credited without a real run."
        hit, miss = ([], ["submit a passing solution"]) if score < 10 else (["passing submission"], [])
    else:
        score, hit, miss = _score_answer(step, text)
        fb = (f"Covered: {', '.join(hit)}." if hit else "") + (f" Missing: {', '.join(miss)}." if miss else "")
        from .agents import grade_interview_answer
        g = grade_interview_answer(db, p, s.slug, step["dimension"], step["q"], text, score, hit, miss)
        if g:
            graded = "llm"
            score, fb = g["score"], g["feedback"] + (f" **Follow-up:** {g['follow_up']}" if g["follow_up"] else "")
    words = len(re.findall(r"\w+", text))
    ans = list(s.answers or [])
    ans.append({"dimension": step["dimension"], "question": step["q"], "answer": text, "score": score, "hit": hit, "miss": miss, "feedback": fb.strip(), "words": words,
                "graded_by": graded})
    s.answers = ans
    s.step += 1
    if s.step >= len(steps):
        finish_interview(db, p, s)
    db.commit()
    return interview_state(s) | {"last_feedback": ans[-1]}


REC = {
    "Problem understanding": "Restate the input, output and constraints before coding; confirm one example out loud.",
    "Approach": "Lead with the key idea in one sentence before details.",
    "Brute force": "Always name the brute force and its cost first — it shows you can find *a* solution.",
    "Optimization": "Name the repeated work in the brute force, then the variable/structure that removes it.",
    "Data structure selection": "Justify the structure by the operation you need (e.g. O(1) lookup, LIFO).",
    "Time complexity": "State Big-O and *why* (number of passes × work per element).",
    "Space complexity": "Count only extra memory you allocate; say 'constant' or 'linear' explicitly.",
    "Edge cases": "List 3 edge cases: empty/single element, all same, extreme order (all decreasing/negative).",
    "Code correctness": "Submit in the Practice Arena until all tests pass before the mock.",
    "Communication": "Use connectors (because / so / which means) and finish with complexity.",
}


def finish_interview(db, p, s: InterviewSession) -> None:
    ans = s.answers or []
    scores = {a["dimension"]: a["score"] for a in ans}
    # communication blends the summary answer with structure across all answers
    avg_words = sum(a["words"] for a in ans) / max(1, len(ans))
    structure = 10 if avg_words >= 12 else 7 if avg_words >= 7 else 4
    scores["Communication"] = round(0.6 * scores.get("Communication", 0) + 0.4 * structure, 1)
    overall = round(sum(scores.values()) / len(scores), 1)
    strengths = [d for d, v in scores.items() if v >= 7]
    weak = [d for d, v in scores.items() if v < 5]
    s.scores, s.status = scores, "complete"
    # compare to baseline for improvement tracking
    base = db.query(InterviewSession).filter_by(user_id=p.id, is_baseline=True).first()
    improvement = {}
    if base and base.scores:
        for d in ("Time complexity", "Space complexity", "Communication"):
            if d in base.scores:
                improvement[d] = round(scores.get(d, 0) - base.scores[d], 1)
    s.report = {"overall": overall, "scores": scores, "strengths": strengths, "weaknesses": weak,
                "recommendations": [REC[d] for d in weak] or ["Repeat the mock on a new problem tomorrow; aim for ≥ 8 everywhere."],
                "improvement_vs_baseline": improvement,
                "summary": f"Overall {overall}/10 on {PROBLEMS[s.slug]['title']}. " + (f"Strong: {', '.join(strengths[:3])}. " if strengths else "") + (f"Work on: {', '.join(weak[:3])}." if weak else "")}
    pr = PROBLEMS[s.slug]
    for d in weak:
        cat = "Complexity Error" if "complexity" in d.lower() else "Communication Issue" if d == "Communication" else "Edge Case Error" if d == "Edge cases" else "Pattern Recognition" if d in ("Approach", "Optimization", "Data structure selection") else "Conceptual Misunderstanding"
        record_mistake(db, p, cat, s.slug, pr["topics"][0], f"Mock interview: weak {d.lower()}", f"Scored {scores[d]}/10. {REC[d]}",
                       {"session": s.id, "score": scores[d]}, source="interview")
    for d in ("Time complexity", "Space complexity", "Communication"):
        if scores.get(d, 0) >= 7:
            for m in db.query(MistakeRecord).filter_by(user_id=p.id, source="seed-baseline").all():
                if (d == "Communication" and m.dna_group == "communication") or ("complexity" in d.lower() and m.dna_group == "complexity"):
                    m.status = "improving" if scores[d] < 9 else "resolved"
                    m.evidence = (m.evidence or {}) | {"latest_score": scores[d], "session": s.id}
    pe.mark_task(db, p.id, "communication", s.slug)
    pe.award(db, p, "interview", 60, 15, {"session": s.id, "overall": overall})


# ------------------------------------------------------------------ analytics
def analytics(db, p) -> dict:
    recs = db.query(ProgressRecord).filter_by(user_id=p.id).all()
    days = [(clock.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    by_day = defaultdict(lambda: {"xp": 0, "minutes": 0})
    for r in recs:
        by_day[r.day]["xp"] += r.xp
        by_day[r.day]["minutes"] += r.minutes
    subs = db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit").all()
    status = Counter(s.status for s in subs)
    topic_acc = defaultdict(lambda: [0, 0])
    for s in subs:
        for t in PROBLEMS[s.slug]["topics"]:
            topic_acc[t][1] += 1
            topic_acc[t][0] += s.status == "Accepted"
    cur = db.query(UserCurriculum).filter_by(user_id=p.id).order_by(UserCurriculum.order).all()
    ms = db.query(MistakeRecord).filter_by(user_id=p.id).all()
    ivs = db.query(InterviewSession).filter_by(user_id=p.id, status="complete").order_by(InterviewSession.id).all()
    return {
        "weekly": [{"day": d[5:], "xp": by_day[d]["xp"], "minutes": round(by_day[d]["minutes"], 1)} for d in days],
        "submissions": {"total": len(subs), **status},
        "topic_accuracy": [{"topic": t, "accuracy": round(100 * a / n), "attempts": n} for t, (a, n) in topic_acc.items()],
        "mastery": [{"topic": c.topic, "mastery": round(c.mastery * 100), "status": c.status} for c in cur],
        "mistakes": Counter(m.category for m in ms),
        "interviews": [{"id": i.id, "baseline": i.is_baseline, "overall": (i.report or {}).get("overall"), "scores": i.scores} for i in ivs],
        "progress": pe.preparation_progress(db, p),
        "xp": p.xp, "streak": p.streak,
    }
