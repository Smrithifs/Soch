"""Company personalisation, calendar day detail and Mock OA review (agent + offline fallback)."""
import json
import time
from datetime import date, timedelta

from sqlalchemy.orm import Session

from database.models import DailyTask, MistakeRecord, RevisionCard, StudentProfile, UserCurriculum, UserProblemHistory
from . import clock, executor, llm, memory_model as mm, personalization_engine as pe, tutor_engine
from .agents import _student, _trace
from .knowledge import CARDS, KB, TOPIC_CARDS
from .problem_bank import PROBLEMS

# ------------------------------------------------------------------ companies
# Representative, publicly-known preparation patterns — not confidential questions.
COMPANIES = {
    "amazon": {"name": "Amazon", "oa": "Online assessment usually has 2 coding questions (~90 min), often followed by a work-style survey.",
               "interview": "Loops combine DSA rounds with Leadership Principles questions — every answer should show impact.",
               "focus": ["Arrays", "Hashing", "Trees and BST", "Graphs", "Dynamic Programming"],
               "tips": ["Explain trade-offs out loud; Amazon interviewers grade reasoning, not just the answer",
                        "Prepare 2–3 STAR stories (Ownership, Dive Deep, Bias for Action)", "Hit edge cases before declaring done"]},
    "microsoft": {"name": "Microsoft", "oa": "OA on Codility/HackerRank style platforms, 2–3 problems.",
                  "interview": "Internship loops: 1–3 technical rounds on DSA plus discussion of projects.",
                  "focus": ["Arrays", "Hashing", "Stacks and Queues", "Trees and BST", "Strings"],
                  "tips": ["Think aloud: restate → brute force → optimise", "Always state time and space complexity", "Write clean, readable code — naming matters"]},
    "google": {"name": "Google", "oa": "Online challenge with 2 algorithmic problems for interns/new grads.",
               "interview": "45-minute rounds in a shared doc; strong focus on optimal complexity and clean reasoning.",
               "focus": ["Graphs", "Dynamic Programming", "Arrays", "Binary Search", "Trees and BST"],
               "tips": ["Clarify constraints first — they decide the algorithm", "Code without an IDE; practise in plain text", "Test with your own small example out loud"]},
    "zscaler": {"name": "Zscaler", "oa": "Online assessment with ~2 coding questions plus MCQs on CS fundamentals.",
                "interview": "Technical rounds on DSA, OS/networking basics for some roles.",
                "focus": ["Stacks and Queues", "Arrays", "Strings", "Hashing"],
                "tips": ["Read all questions first; bank the easier one", "Handle empty / single-element inputs", "Revise networking basics (TCP/HTTP) if the role is infra/security"]},
    "flipkart": {"name": "Flipkart", "oa": "OA with 2–3 medium problems; machine-coding round for SDE roles.",
                 "interview": "DSA + problem-solving rounds; machine coding tests clean, extensible design.",
                 "focus": ["Arrays", "Hashing", "Graphs", "Dynamic Programming", "Heaps"],
                 "tips": ["Practise one 90-minute machine-coding exercise", "Medium DP and graphs appear often", "Explain design choices clearly"]},
    "adobe": {"name": "Adobe", "oa": "OA with coding + aptitude/CS MCQs.", "interview": "DSA rounds plus OOP and project deep-dives.",
              "focus": ["Arrays", "Strings", "Linked Lists", "Trees and BST"], "tips": ["Revise OOP principles", "Be ready to explain your projects in depth"]},
    "goldman sachs": {"name": "Goldman Sachs", "oa": "HackerRank OA: coding + quantitative/aptitude sections.", "interview": "DSA, probability puzzles and CS fundamentals.",
                      "focus": ["Arrays", "Dynamic Programming", "Hashing", "Greedy"], "tips": ["Practise basic probability", "Be precise with edge cases and overflow"]},
}


def company_view(db: Session, p: StudentProfile) -> dict:
    key = (p.company or "").strip().lower()
    base = COMPANIES.get(key)
    name = base["name"] if base else (p.company or "").strip().title() or None
    if not base:
        base = {"oa": f"No stored profile for {name} yet — SOCH uses the most common OA/interview patterns." if name else "No company selected.",
                "interview": "Typical DSA rounds: arrays, hashing, trees, graphs, DP.",
                "focus": ["Arrays", "Hashing", "Trees and BST", "Dynamic Programming"], "tips": ["Master the top patterns first", "Time yourself on every practice problem"]}
    track = pe.select_track(p)
    mem = {m["topic"]: m for m in mm.snapshot(db, p.id)}
    solved = {h.slug for h in db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit", status="Accepted")}
    focus = []
    for t in base["focus"]:
        t = mm.norm(t)
        m = mem.get(t)
        practiced = [PROBLEMS[s]["title"] for s in solved if mm.norm(PROBLEMS[s]["topics"][0]) == t]
        status = m["status"] if m else ("not started" if not practiced else "strong")
        focus.append({"topic": t, "status": status, "retention": m["retention"] if m else None, "solved": practiced,
                      "weak": t in [mm.norm(x) for x in (p.weak_topics or [])]})
    gaps = [f["topic"] for f in focus if f["status"] in ("not started", "forgotten", "fading") or f["weak"]]
    covered = len([f for f in focus if f["status"] == "strong"])
    picks = pe.select_problems(db, p, 5)
    dl = pe.days_left(p)
    stage = "OA" if track == "oa" else "interview" if track == "interview" else "preparation"
    brief_obs = {"company": name, "stage": stage, "days_left": dl, "minutes_per_day": p.daily_minutes, "level": p.level,
                 "focus_status": [{k: f[k] for k in ("topic", "status", "retention")} for f in focus], "solved": sorted(solved)}
    t0 = time.time()
    try:
        brief = llm.chat([{"role": "system", "content": "You are a placement coach. In 3 short sentences (max 75 words), tell this student how to prepare for "
                           "this company given their status. Be specific to the data. Do not claim to know confidential questions."},
                          {"role": "user", "content": json.dumps(brief_obs)}], temperature=0.4, max_tokens=180)
        src = "llm"
    except llm.LLMUnavailable:
        src = "fallback"
        brief = (f"{name or 'Your target'} {stage}" + (f" is in {dl} day{'s' if dl != 1 else ''}" if dl is not None else "") +
                 f". You're solid on {covered}/{len(focus)} of its core topics. " +
                 (f"Close the gaps first: {', '.join(gaps[:3])}. " if gaps else "Keep them warm with timed practice. ") +
                 f"With {p.daily_minutes} min/day, do one timed problem plus one recall card daily.")
    _trace(db, p.id, "Company Coach", f"{name} brief", brief_obs, {"brief": brief}, src, t0)
    db.commit()
    return {"company": name, "known": key in COMPANIES, "stage": stage, "days_left": dl, "format": base["oa"] if track == "oa" else base["interview"],
            "other_round": base["interview"] if track == "oa" else base["oa"], "tips": base["tips"], "focus": focus, "gaps": gaps,
            "coverage": round(100 * covered / max(1, len(focus))), "brief": brief, "brief_source": src, "role": p.role,
            "problems": [{"slug": s, "title": PROBLEMS[s]["title"], "difficulty": PROBLEMS[s]["difficulty"], "topic": PROBLEMS[s]["topics"][0],
                          "solved": s in solved, "why": w} for s, w in picks],
            "disclaimer": "Representative preparation guidance from public patterns — not confidential or official company questions."}


# ------------------------------------------------------------------ calendar day detail
def _topic_for_day(p, i: int) -> str:
    track = pe.select_track(p)
    if track == "oa":
        seq = ["Stacks and Queues", "Arrays", "Hashing", "Arrays", "Dynamic Programming", "Arrays", "Hashing"]
    elif track == "interview":
        seq = [mm.norm(t) for t in (p.revise_topics or ["Arrays", "Hashing", "Stacks"])] or ["Arrays"]
    else:
        seq = [mm.norm(p.starting_topic or "Hashing"), "Arrays", "Time Complexity"]
    return seq[i % len(seq)]


def day_detail(db: Session, p: StudentProfile, day: str) -> dict:
    d = date.fromisoformat(day)
    i = (d - clock.today()).days
    ev = p.event_date and day == p.event_date
    if i < 0:
        recs = db.query(UserProblemHistory).filter(UserProblemHistory.user_id == p.id).all()
        done = [r for r in recs if r.created_at.date() == d and r.kind == "submit"]
        return {"date": day, "kind": "past", "title": "Completed", "tasks": [{"kind": "problem", "title": PROBLEMS[r.slug]["title"], "minutes": None,
                "detail": f"{r.status} ({r.passed}/{r.total})", "ref": r.slug} for r in done], "note": "History for this day." if done else "No activity recorded."}
    if ev:
        return {"date": day, "kind": "event", "title": f"{COMPANIES.get((p.company or '').strip().lower(), {}).get('name') or (p.company or '').strip().title()} {'Online Assessment' if p.track == 'oa' else 'Interview'}".strip(),
                "tasks": [{"kind": "event", "title": "Light warm-up: 1 easy problem you've solved before", "minutes": 10, "detail": "Confidence, not learning."},
                          {"kind": "event", "title": "Skim your Mistake DNA", "minutes": 5, "detail": "Remember the traps you've fallen into."}],
                "note": "Sleep well the night before. No new topics today."}
    if i == 0:
        plan = pe.get_today(db, p)
        return {"date": day, "kind": "today", "title": "Today", "rule": plan["rule"], "total_minutes": plan["total_minutes"],
                "tasks": [{"kind": t["kind"], "title": t["title"], "minutes": t["minutes"], "detail": t["reason"], "ref": t["ref"], "done": t["done"]} for t in plan["tasks"]]}
    # future: project the plan with the same rules
    topic = _topic_for_day(p, i)
    b = pe.time_budget(p, p.daily_minutes)
    tasks = []
    # topics whose memory will be forgotten by that day → recall first
    for m in mm.snapshot(db, p.id):
        if m["forgotten_in_days"] <= i:
            tasks.append({"kind": "recall", "title": f"Recall: {m['topic']}", "minutes": 5,
                          "detail": f"By this day {m['topic']} is projected below 45% retention — retrieve it before it's gone."})
            break
    cands = [s for s in PROBLEMS if mm.norm(PROBLEMS[s]["topics"][0]) == topic] or list(PROBLEMS)
    solved = {h.slug for h in db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit", status="Accepted")}
    cands = sorted(cands, key=lambda s: (s in solved, PROBLEMS[s]["learning_order"]))
    for s in cands[: max(1, b["problems"])] if b["problems"] else []:
        tasks.append({"kind": "problem", "title": PROBLEMS[s]["title"], "minutes": b["problem_min"], "ref": s,
                      "detail": f"{PROBLEMS[s]['difficulty']} · {PROBLEMS[s]['pattern']}" + (" · re-solve from memory" if s in solved else "")})
    for k in TOPIC_CARDS.get(topic, [])[: max(1, b["cards"])]:
        tasks.append({"kind": "revision", "title": CARDS[k]["concept"], "minutes": b["card_min"], "ref": k, "detail": f"{CARDS[k]['topic']} recall card"})
    if pe.select_track(p) == "interview":
        tasks.append({"kind": "communication", "title": "Mock interview" if i >= 2 else "Explain approaches aloud", "minutes": 5,
                      "detail": "Talk through approach → complexity → edge cases."})
    return {"date": day, "kind": "future", "title": f"Focus: {topic}", "rule": b["rule"], "total_minutes": round(sum((t["minutes"] or 0) for t in tasks), 1),
            "tasks": tasks, "note": "Projected — it adapts automatically to what you actually do before then."}


def calendar_month(db: Session, p: StudentProfile, year: int, month: int) -> dict:
    first = date(year, month, 1)
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    today = clock.today()
    activity = {}
    for r in db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit").all():
        k = r.created_at.date().isoformat()
        activity[k] = activity.get(k, 0) + 1
    days = []
    d = first
    while d < nxt:
        i = (d - today).days
        k = d.isoformat()
        tag = "event" if k == p.event_date else "today" if i == 0 else "past" if i < 0 else "plan"
        focus = _topic_for_day(p, i) if i > 0 else None
        days.append({"date": k, "tag": tag, "focus": focus, "activity": activity.get(k, 0)})
        d += timedelta(days=1)
    return {"year": year, "month": month, "today": today.isoformat(), "event_date": p.event_date, "days": days}


# ------------------------------------------------------------------ Mock OA review
OA_SYS = """You are an OA reviewer. For ONE question you get: the problem, the student's code, the REAL test results from a compiler,
static analysis and known bug patterns. Write a review the student can learn from. Never invent test results.
Reply JSON: {"verdict": "<one line>", "what_went_wrong": "<1-3 sentences, specific to their code; empty if fully correct>",
"what_went_well": "<1 sentence>", "fix": "<the concrete change / idea, no full solution>", "concept_gap": "<topic or concept to revise, or empty>"}"""


def mock_oa_finish(db: Session, p: StudentProfile, items: list[dict], seconds_used: int) -> dict:
    from .learning_services import record_submission
    reviews, weak = [], []
    for it in items:
        slug, code = it["slug"], it.get("code") or ""
        prob = PROBLEMS[slug]
        untouched = code.strip() == prob["starter"]["java"].strip() or not code.strip()
        res = executor.submit_code(slug, "java", code) if not untouched else {"status": "Not attempted", "passed": 0, "total": len(prob["tests"]), "tests": []}
        if not untouched:
            record_submission(db, p, slug, "java", code, "submit", res)
        a = tutor_engine.analyze_code(code)
        bugs = tutor_engine.detect_bugs(slug, code, res) if not untouched else []
        ff = res.get("first_failure") or {}
        t0 = time.time()
        rv = None
        if not untouched and res["status"] != "Accepted":
            try:
                out = llm.chat([{"role": "system", "content": OA_SYS},
                                {"role": "user", "content": json.dumps({"problem": prob["title"], "statement": prob["statement"], "student_code": code[:3500],
                                                                        "real_result": {"status": res["status"], "passed": res.get("passed"), "total": res.get("total"),
                                                                                        "first_failing_test": {k: ff.get(k) for k in ("input", "expected", "actual", "stderr")} if ff else None,
                                                                                        "compiler_error": (res.get("stderr") or "")[:500]},
                                                                        "static": {"time": a["time"], "space": a["space"]}, "known_bugs": bugs,
                                                                        "reference": KB[slug]["optimal"]})}], want_json=True, temperature=0.2, max_tokens=400)
                rv = {k: str(out.get(k, "")) for k in ("verdict", "what_went_wrong", "what_went_well", "fix", "concept_gap")} | {"source": "llm"}
            except llm.LLMUnavailable:
                rv = None
        if rv is None:
            if untouched:
                rv = {"verdict": "Not attempted", "what_went_wrong": "No code was written for this question.", "what_went_well": "",
                      "fix": f"Start from the pattern: {prob['pattern']}. {KB[slug]['hints'][0]}", "concept_gap": prob["topics"][0]}
            elif res["status"] == "Accepted":
                rv = {"verdict": f"Accepted — {res['passed']}/{res['total']} tests", "what_went_wrong": "" if a["time"] == prob["complexity"]["time"] else
                      f"Correct, but your code is {a['time']} vs optimal {prob['complexity']['time']} — it may time out on large inputs.",
                      "what_went_well": f"Correct use of {prob['pattern'].lower()}.", "fix": "" if a["time"] == prob["complexity"]["time"] else KB[slug]["optimal"],
                      "concept_gap": "" if a["time"] == prob["complexity"]["time"] else "Time Complexity"}
            else:
                where = (f"Fails on `{ff.get('input')}` — expected `{ff.get('expected')}`, got `{ff.get('actual') or ff.get('status')}`. " if ff else "") + \
                        (bugs[0] if bugs else "")
                if res["status"] == "Compilation Error":
                    where = "Doesn't compile: " + (res.get("stderr") or "").splitlines()[0][:200] if res.get("stderr") else "Doesn't compile."
                rv = {"verdict": f"{res['status']} — {res.get('passed', 0)}/{res.get('total')} tests",
                      "what_went_wrong": where.strip() or "Output differs on hidden tests.",
                      "what_went_well": f"Passed {res.get('passed', 0)} test(s)." if res.get("passed") else "",
                      "fix": KB[slug]["hints"][min(2, 1 + (res.get("passed", 0) == 0))], "concept_gap": prob["topics"][0]}
            rv["source"] = "fallback"
        _trace(db, p.id, "OA Reviewer", f"{prob['title']}: {res['status']}", {"status": res["status"], "passed": res.get("passed"), "first_failure": ff or None},
               rv, rv["source"], t0)
        if res["status"] != "Accepted":
            weak.append(mm.norm(prob["topics"][0]))
        elif rv.get("concept_gap"):
            weak.append(mm.norm(rv["concept_gap"]))
        reviews.append({"slug": slug, "title": prob["title"], "difficulty": prob["difficulty"], "topic": prob["topics"][0], "status": res["status"],
                        "passed": res.get("passed", 0), "total": res.get("total", len(prob["tests"])), "time": a["time"], "space": a["space"],
                        "first_failure": ff or None, "review": rv})
    # ---- feed weak areas into the roadmap / plan
    weak = list(dict.fromkeys([w for w in weak if w]))
    p.weak_topics = list(dict.fromkeys([*(p.weak_topics or []), *weak]))
    added = []
    for w in weak:
        row = db.query(UserCurriculum).filter_by(user_id=p.id, topic=w).first()
        if row:
            if row.status != "current":
                row.status = "revise"
            row.mastery = max(0.0, round(row.mastery - 0.1, 3))
        for k in TOPIC_CARDS.get(w, [])[:2]:
            c = db.query(RevisionCard).filter_by(user_id=p.id, card_key=k).first()
            if not c:
                c = RevisionCard(user_id=p.id, card_key=k, topic=CARDS[k]["topic"], concept=CARDS[k]["concept"])
                db.add(c)
            c.due_at = clock.now()
            added.append(CARDS[k]["concept"])
    total = sum(r["passed"] for r in reviews)
    possible = sum(r["total"] for r in reviews) or 1
    score = round(100 * total / possible)
    solved_n = sum(r["status"] == "Accepted" for r in reviews)
    pe.award(db, p, "mock_oa", 20 + 10 * solved_n, seconds_used / 60, {"score": score})
    db.commit()
    pe.generate_daily_schedule(db, p)
    return {"score": score, "solved": solved_n, "total_questions": len(reviews), "minutes_used": round(seconds_used / 60, 1), "reviews": reviews,
            "weak_topics": weak, "roadmap_update": {"topics_marked_revise": weak, "revision_cards_due": added}}
