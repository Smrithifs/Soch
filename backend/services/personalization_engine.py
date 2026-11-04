"""Deterministic personalization rules. Every decision is a pure function of profile + stored history."""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from database.models import (DailyTask, InterviewSession, MistakeRecord, ProgressRecord, RevisionCard, StudentProfile, UserCurriculum,
                             UserPreferences, UserProblemHistory)
from .knowledge import CARDS, ROADMAP, TOPIC_ALIASES, TOPIC_CARDS
from .problem_bank import PROBLEMS
from . import clock

TRACK_LABEL = {"oa": "Online Assessment", "interview": "Technical Interviews", "learning": "DSA Learning"}
CARD_MIN = 1.5      # one recall card
OA_REVISION_MIN = 5  # OA's "short revision activity"
COMM_MIN = 3        # communication drill
INTERVIEW_CLOSE_DAYS = 7


def today() -> str:
    return clock.today().isoformat()


# ------------------------------------------------------------------ basic selectors
def select_track(p: StudentProfile) -> str:
    return p.track if p.track in TRACK_LABEL else "learning"


def available_minutes(db: Session, p: StudentProfile) -> int:
    pref = db.query(UserPreferences).filter_by(user_id=p.id).first()
    return int(pref.active_minutes) if pref and pref.active_minutes else int(p.daily_minutes or 20)


def days_left(p: StudentProfile) -> int | None:
    if p.event_date:
        try:
            return max(0, (date.fromisoformat(p.event_date) - clock.today()).days)
        except ValueError:
            pass
    return p.days_remaining


def norm_topic(t: str) -> str:
    return TOPIC_ALIASES.get(t, t)


def time_budget(p: StudentProfile, minutes: int) -> dict:
    """Explicit time rules from the spec. Returns counts + minutes per item + rule text."""
    track, dl = select_track(p), days_left(p)
    if minutes < 8:
        return {"problems": 0, "problem_min": 0, "cards": min(3, max(1, int(minutes // CARD_MIN))), "card_min": CARD_MIN, "comm": 0,
                "rule": f"{minutes} min < 8 min → revision only (not enough time to read, code and test a new problem)."}
    if minutes < 20:
        pm = 8 if minutes < 12 else 9
        cards = min(3, int((minutes - pm) // 2))
        return {"problems": 1, "problem_min": pm, "cards": cards, "card_min": 2, "comm": 0,
                "rule": f"8–19 min → one coding problem ({pm} min) plus {cards} revision activit{'y' if cards == 1 else 'ies'}."}
    if track == "oa":
        n = max(1, min(p.questions_expected or 2, (minutes - OA_REVISION_MIN) // 10))
        return {"problems": n, "problem_min": 10, "cards": 1, "card_min": minutes - 10 * n, "comm": 0,
                "rule": f"OA, {minutes} min, {p.questions_expected or 2} questions expected → {n} timed problems × 10 min + 1 short revision."}
    if track == "interview":
        if dl is not None and dl <= INTERVIEW_CLOSE_DAYS:
            cards = min(8, int((minutes - 8 - COMM_MIN) // CARD_MIN))
            return {"problems": 1, "problem_min": 8, "cards": cards, "card_min": CARD_MIN, "comm": 1,
                    "rule": f"Interview in {dl} day(s) (≤ {INTERVIEW_CLOSE_DAYS}) → revision-heavy: 1 problem, {cards} recall cards, 1 communication drill."}
        n = 2 if minutes >= 35 else 1
        return {"problems": n, "problem_min": 12, "cards": int((minutes - 12 * n) // 2), "card_min": 2, "comm": 0,
                "rule": f"Interview > {INTERVIEW_CLOSE_DAYS} days away → {n} new problem(s) + revision."}
    n = 2 if minutes >= 35 else 1
    return {"problems": n, "problem_min": 9, "cards": min(4, int((minutes - 9 * n) // 2)), "card_min": 2, "comm": 0,
            "rule": f"Learning track, {minutes} min → {n} new problem(s) + revision of prerequisite concepts."}


# ------------------------------------------------------------------ topic priority & problems
def prioritize_topics(db: Session, p: StudentProfile) -> list[str]:
    """Order: topics with open mistakes > declared weak/revise topics > current curriculum topic > rest."""
    from . import memory_model as mm
    decayed = [m["topic"] for m in mm.snapshot(db, p.id) if m["status"] != "strong"]  # lowest retention first
    mistakes = decayed + [m.topic for m in db.query(MistakeRecord).filter_by(user_id=p.id, status="open").all() if m.topic]
    declared = [norm_topic(t) for t in (p.weak_topics or []) + (p.revise_topics or [])]
    cur = db.query(UserCurriculum).filter_by(user_id=p.id, status="current").first() if select_track(p) == "learning" else None
    out = []
    for t in mistakes + declared + ([cur.topic] if cur else []) + ([norm_topic(p.starting_topic)] if p.starting_topic else []):
        if t and t not in out:
            out.append(t)
    return out


def _solved(db, uid) -> set[str]:
    return {h.slug for h in db.query(UserProblemHistory).filter_by(user_id=uid, kind="submit", status="Accepted").all()}


def _failed(db, uid) -> set[str]:
    return {h.slug for h in db.query(UserProblemHistory).filter_by(user_id=uid, kind="submit").all() if h.status != "Accepted"} - _solved(db, uid)


def score_problem(db, p: StudentProfile, slug: str, prio: list[str]) -> tuple[float, list[str]]:
    """Deterministic score with human-readable reasons."""
    pr, track, why = PROBLEMS[slug], select_track(p), []
    topics = [norm_topic(t) for t in pr["topics"]]
    s = 0.0
    matched = [t for t in topics if t in prio or any(norm_topic(x) == t for x in (p.revise_topics or []))]
    if matched:
        s += 10
        why.append(f"covers your priority topic {matched[0]}")
    cw = {k.lower(): v for k, v in pr["company_weight"].items()}.get((p.company or "").strip().lower(), 0)
    if cw:
        s += cw
        why.append(f"{p.company} weight {cw}/5")
    if track == "oa":
        s += pr["oa_frequency"]
        why.append(f"OA pattern frequency {pr['oa_frequency']}/10")
    elif track == "interview":
        s += pr["interview_frequency"] * 0.1
        why.append(f"interview frequency {pr['interview_frequency']}/10")
        if slug in _failed(db, p.id):
            s += 50
            why.append("previously failed → retry first")
    else:
        start = norm_topic(p.starting_topic or "Arrays")
        if start in topics:
            s += 20 - pr["learning_order"]
            why.append(f"first problems of your current topic {start}")
    if p.level == "Beginner" and pr["difficulty"] == "Hard":
        s -= 20
    if slug in _solved(db, p.id):
        s -= 30
    return s, why


def select_problems(db: Session, p: StudentProfile, count: int) -> list[tuple[str, list[str]]]:
    if count <= 0:
        return []
    prio = prioritize_topics(db, p)
    ranked = sorted(PROBLEMS, key=lambda sl: (-score_problem(db, p, sl, prio)[0], sl))
    return [(sl, score_problem(db, p, sl, prio)[1]) for sl in ranked[:count]]


def next_problem(db: Session, p: StudentProfile) -> dict:
    """Progression rule: follow the 'next_problem' chain from the most recent accepted (or planned) problem."""
    last = db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit", status="Accepted").order_by(UserProblemHistory.id.desc()).first()
    base = last.slug if last else (select_problems(db, p, 1) or [("two-sum", [])])[0][0]
    nxt = PROBLEMS[base]["next_problem"]
    solved = _solved(db, p.id)
    seen = set()
    while nxt in solved and nxt not in seen:
        seen.add(nxt)
        nxt = PROBLEMS[nxt]["next_problem"]
    return {"slug": nxt, "title": PROBLEMS[nxt]["title"],
            "reason": f"After {PROBLEMS[base]['title']}, {PROBLEMS[nxt]['title']} reuses {PROBLEMS[nxt]['topics'][0]} with a new pattern: {PROBLEMS[nxt]['pattern']}."}


# ------------------------------------------------------------------ revision cards
def ensure_cards(db: Session, p: StudentProfile) -> None:
    keys = set()
    for t in revision_topics(p):
        keys.update(TOPIC_CARDS.get(t, []))
    have = {c.card_key for c in db.query(RevisionCard).filter_by(user_id=p.id).all()}
    for k in sorted(keys - have, key=list(CARDS).index):
        db.add(RevisionCard(user_id=p.id, card_key=k, topic=CARDS[k]["topic"], concept=CARDS[k]["concept"], due_at=clock.now()))
    db.flush()


def revision_topics(p: StudentProfile) -> list[str]:
    track = select_track(p)
    if track == "learning":
        start = norm_topic(p.starting_topic or "Arrays")
        prereq = next((pr for t, pr, _ in ROADMAP if t == start), [])
        return list(dict.fromkeys(prereq + [start, "Time Complexity"]))
    if track == "interview":
        return [norm_topic(t) for t in (p.revise_topics or ["Arrays", "Hashing", "Stacks"])]
    return list(dict.fromkeys([norm_topic(t) for t in (p.weak_topics or [])] + ["Stacks and Queues", "Arrays"]))


def card_priority(db: Session, p: StudentProfile, c: RevisionCard) -> tuple[float, list[str]]:
    """Higher = sooner. Uses due time, mistakes, mastery, hint usage and accuracy."""
    why, s = [], 0.0
    overdue_h = (clock.now() - (c.due_at or clock.now())).total_seconds() / 3600
    if overdue_h >= 0:
        s += 5 + min(overdue_h / 24, 5)
        why.append("due now")
    else:
        s -= 10
    if c.last_result == "wrong":
        s += 15
        why.append("you missed it last time")
    if db.query(MistakeRecord).filter_by(user_id=p.id, topic=c.topic, status="open").count():
        s += 6
        why.append(f"open mistake in {c.topic}")
    cur = db.query(UserCurriculum).filter_by(user_id=p.id, topic=norm_topic(c.topic)).first()
    if cur:
        s += (1 - cur.mastery) * 3
    pref = db.query(UserPreferences).filter_by(user_id=p.id).first()
    hints = sum((pref.hint_levels or {}).values()) if pref else 0
    if hints and c.topic in ("Hashing", "Stacks", "Arrays"):
        s += min(hints, 3)
        why.append("hints used on related problems")
    if c.attempts:
        s += (1 - c.correct / c.attempts) * 4
    order = revision_topics(p)
    t = norm_topic(c.topic)
    s -= (order.index(t) if t in order else 9) * 0.5 + list(CARDS).index(c.card_key) * 0.01  # deterministic tiebreak
    return s, why


def choose_revision_activities(db: Session, p: StudentProfile, count: int) -> list[tuple[RevisionCard, list[str]]]:
    ensure_cards(db, p)
    cards = db.query(RevisionCard).filter_by(user_id=p.id).all()
    track = select_track(p)
    scored = sorted(((card_priority(db, p, c), c) for c in cards), key=lambda x: -x[0][0])
    if track == "learning" or track == "interview":
        # spread across topics first (one per topic), then fill
        picked, used = [], set()
        for (s, why), c in scored:
            if c.topic not in used:
                picked.append((c, why)); used.add(c.topic)
        for (s, why), c in scored:
            if c not in [x[0] for x in picked]:
                picked.append((c, why))
        return picked[:count]
    return [(c, why) for (s, why), c in scored[:count]]


# ------------------------------------------------------------------ daily plan
def generate_daily_schedule(db: Session, p: StudentProfile, minutes: int | None = None) -> dict:
    minutes = minutes or available_minutes(db, p)
    b = time_budget(p, minutes)
    prev = db.query(DailyTask).filter_by(user_id=p.id, day=today()).order_by(DailyTask.position).all()
    old = {(t.kind, t.ref): t.done for t in prev}
    # Stability rule: problems already assigned today keep their slot when time changes (same-day replans).
    kept = [t.ref for t in prev if t.kind == "problem"][: b["problems"]]
    db.query(DailyTask).filter_by(user_id=p.id, day=today()).delete()
    tasks, pos = [], 0
    dl = days_left(p)
    fresh = [x for x in select_problems(db, p, b["problems"] + len(kept)) if x[0] not in kept]
    picks = [(sl, score_problem(db, p, sl, prioritize_topics(db, p))[1]) for sl in kept] + fresh
    # Memory rule: if a topic you've already solved has dropped into the 'forgotten' band, today opens with a recall rescue.
    from . import memory_model as mm
    solved_by_topic = {}
    for h in db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit", status="Accepted").order_by(UserProblemHistory.id):
        solved_by_topic[mm.norm(PROBLEMS[h.slug]["topics"][0])] = h.slug
    for m in mm.snapshot(db, p.id):
        if m["status"] == "forgotten" and m["topic"] in solved_by_topic and minutes >= 8:
            sl = solved_by_topic[m["topic"]]
            tasks.append(DailyTask(user_id=p.id, day=today(), position=pos, kind="recall", ref=sl, title=f"Recall Rescue: {PROBLEMS[sl]['title']}",
                                   minutes=5, reason=f"**{m['topic']}** is down to {m['retention']}% retention ({m['days_since']:g} day{'s' if m['days_since'] != 1 else ''} since you last used it). "
                                                      "Rebuild it from memory before learning anything new."))
            pos += 1
            b = dict(b, cards=max(0, b["cards"] - 2))
            break
    for slug, why in picks[: b["problems"]]:
        pr = PROBLEMS[slug]
        if select_track(p) == "oa":
            reason = f"{p.company} OA in {dl} days with {p.questions_expected} coding questions: drill **{pr['pattern']}** under a {b['problem_min']}-min timer ({', '.join(why)})."
        elif select_track(p) == "interview":
            reason = f"{p.company} interview in {dl} days: a high-frequency {pr['topics'][0]} problem you must be able to explain aloud ({', '.join(why)})."
        else:
            reason = f"Introduces {pr['pattern']} — the core idea of {norm_topic(p.starting_topic)} ({', '.join(why)})."
        tasks.append(DailyTask(user_id=p.id, day=today(), position=pos, kind="problem", ref=slug, title=pr["title"], minutes=b["problem_min"], reason=reason))
        pos += 1
    for c, why in choose_revision_activities(db, p, b["cards"]):
        reason = f"Reinforces **{c.concept}** ({c.topic})" + (f" — {', '.join(why)}." if why else ".")
        if b["problems"] == 0:
            reason += " Recall-only because time is short."
        tasks.append(DailyTask(user_id=p.id, day=today(), position=pos, kind="revision", ref=c.card_key, title=f"{c.topic} revision: {c.concept}",
                               minutes=b["card_min"] if b["cards"] == 1 and select_track(p) == "oa" else b["card_min"], reason=reason))
        pos += 1
    if b["comm"]:
        slug = tasks[0].ref if tasks and tasks[0].kind == "problem" else "two-sum"
        tasks.append(DailyTask(user_id=p.id, day=today(), position=pos, kind="communication", ref=slug,
                               title=f"Explain {PROBLEMS[slug]['title']} aloud in 60 seconds", minutes=COMM_MIN,
                               reason="Interviews grade how you explain, not only the code. One-sentence approach + complexity + one edge case."))
    for t in tasks:
        t.done = old.get((t.kind, t.ref), False)
        db.add(t)
    db.commit()
    return {"minutes": minutes, "rule": b["rule"], "budget": b, "tasks": [task_dict(t) for t in tasks],
            "total_minutes": round(sum(t.minutes for t in tasks), 1)}


def task_dict(t: DailyTask) -> dict:
    return {"id": t.id, "kind": t.kind, "ref": t.ref, "title": t.title, "minutes": t.minutes, "reason": t.reason, "done": t.done}


def get_today(db: Session, p: StudentProfile) -> dict:
    tasks = db.query(DailyTask).filter_by(user_id=p.id, day=today()).order_by(DailyTask.position).all()
    if not tasks:
        return generate_daily_schedule(db, p)
    m = available_minutes(db, p)
    return {"minutes": m, "rule": time_budget(p, m)["rule"], "budget": time_budget(p, m), "tasks": [task_dict(t) for t in tasks],
            "total_minutes": round(sum(t.minutes for t in tasks), 1)}


def mark_task(db: Session, uid: int, kind: str, ref: str) -> None:
    for t in db.query(DailyTask).filter_by(user_id=uid, day=today(), kind=kind, ref=ref).all():
        t.done = True


# ------------------------------------------------------------------ curriculum / mastery
def build_curriculum(db: Session, p: StudentProfile) -> None:
    db.query(UserCurriculum).filter_by(user_id=p.id).delete()
    familiar = {norm_topic(t) for t in (p.familiar_topics or [])}
    start = norm_topic(p.starting_topic or "Arrays")
    months = p.months_available or 6
    total_w = sum(w for *_, w in ROADMAP)
    weeks = months * 4.33
    wk = 0.0
    for i, (t, pre, w) in enumerate(ROADMAP):
        span = weeks * w / total_w
        status = "done" if t in familiar else "current" if t == start else "locked"
        if status == "locked" and all(x in familiar or x == start for x in pre):
            status = "available"
        db.add(UserCurriculum(user_id=p.id, topic=t, order=i, mastery=0.6 if t in familiar else 0.0, status=status, prerequisites=pre,
                              week_start=int(wk) + 1, week_end=max(int(wk) + 1, int(wk + span))))
        wk += span
    # interview / OA students still get mastery rows for their topics
    db.flush()


def update_topic_mastery(db: Session, uid: int, topics: list[str], delta: float) -> None:
    for t in topics:
        t = norm_topic(t)
        row = db.query(UserCurriculum).filter_by(user_id=uid, topic=t).first()
        if not row:
            continue
        row.mastery = round(max(0.0, min(1.0, row.mastery + delta)), 3)
        if delta < 0 and row.status in ("done", "current", "available"):
            row.status = "revise" if row.status == "done" else row.status
        if row.mastery >= 0.8 and row.status in ("current", "revise", "available"):
            row.status = "done"


def adjust_after_mistake(db: Session, p: StudentProfile, m: MistakeRecord) -> None:
    """Rule: a mistake lowers topic mastery, pulls its revision card forward and regenerates today's plan."""
    if m.topic:
        update_topic_mastery(db, p.id, [m.topic], -0.05)
    if m.revision_card:
        c = db.query(RevisionCard).filter_by(user_id=p.id, card_key=m.revision_card).first()
        if not c and m.revision_card in CARDS:
            k = m.revision_card
            c = RevisionCard(user_id=p.id, card_key=k, topic=CARDS[k]["topic"], concept=CARDS[k]["concept"])
            db.add(c)
        if c:
            c.due_at = clock.now()
    db.flush()


# ------------------------------------------------------------------ XP / streak / progress
def award(db: Session, p: StudentProfile, event: str, xp: int, minutes: float = 0, meta: dict | None = None) -> None:
    t = today()
    if p.last_active != t:
        yesterday = (clock.today() - timedelta(days=1)).isoformat()
        p.streak = (p.streak or 0) + 1 if p.last_active == yesterday else 1
        p.last_active = t
    p.xp = (p.xp or 0) + xp
    db.add(ProgressRecord(user_id=p.id, day=t, event=event, xp=xp, minutes=minutes, meta=meta or {}))


def preparation_progress(db: Session, p: StudentProfile) -> dict:
    solved = _solved(db, p.id)
    plan = get_today(db, p)["tasks"]
    planned = [t for t in plan if t["kind"] == "problem"]
    done_tasks = sum(t["done"] for t in plan)
    cards = db.query(RevisionCard).filter_by(user_id=p.id).all()
    attempts = sum(c.attempts for c in cards)
    acc = (sum(c.correct for c in cards) / attempts) if attempts else 0.0
    open_m = db.query(MistakeRecord).filter_by(user_id=p.id, status="open").count()
    track = select_track(p)
    planned_solved = sum(1 for t in planned if t["ref"] in solved)
    if track == "oa":
        target = max(1, p.questions_expected or 2)
        # OA readiness = 55% solving planned OA problems, 25% revision accuracy, 20% minus open mistakes
        readiness = 0.55 * min(1, planned_solved / target) + 0.25 * acc + 0.20 * max(0, 1 - 0.5 * open_m)
    elif track == "interview":
        sess = db.query(InterviewSession).filter_by(user_id=p.id, status="complete", is_baseline=False).order_by(InterviewSession.id.desc()).first()
        iv = (sess.report or {}).get("overall", 0) / 10 if sess else 0
        readiness = 0.35 * min(1, planned_solved / max(1, len(planned))) + 0.25 * acc + 0.30 * iv + 0.10 * max(0, 1 - 0.34 * open_m)
    else:
        cur = db.query(UserCurriculum).filter_by(user_id=p.id).all()
        readiness = sum(c.mastery for c in cur) / max(1, len(cur))
    return {"readiness": round(readiness * 100), "solved": sorted(solved), "tasks_done": done_tasks, "tasks_total": len(plan),
            "revision_accuracy": round(acc * 100), "revision_attempts": attempts, "open_mistakes": open_m}


# ------------------------------------------------------------------ multi-day calendar
def multi_day_plan(db: Session, p: StudentProfile) -> list[dict]:
    track, dl = select_track(p), days_left(p) or 0
    start = clock.today()
    if track == "interview":
        names = [
            ["Arrays, Hashing and Stacks revision", "Best Time to Buy and Sell Stock", "Complexity explanation"],
            ["Re-attempt previously attempted problems", "Explain approaches aloud", "Technical interview simulation"],
            ["Rapid revision", "Edge cases", "Mock interview"],
        ]
        out = [{"date": (start + timedelta(days=i)).isoformat(), "label": f"Day {i+1}", "items": names[i] if i < 3 else ["Rest & light review"]} for i in range(max(3, min(dl, 7)))]
        out.append({"date": p.event_date, "label": "Interview", "items": [f"{p.company} — {p.role}"], "event": True})
        return out
    if track == "oa":
        pats = ["Stacks (bracket matching)", "Kadane / running sums", "Hashing (complement lookup)", "Running min/max (stock)",
                "Timed mixed set (2 problems / 50 min)", "Revise all mistakes", "Light revision + rest"]
        out = [{"date": (start + timedelta(days=i)).isoformat(), "label": f"Day {i+1}", "items": [pats[i % len(pats)], f"{p.daily_minutes} min focused block"]} for i in range(max(1, dl))]
        out.append({"date": p.event_date, "label": "OA day", "items": [f"{(p.company or '').strip().title()} Online Assessment"], "event": True})
        return out
    rows = db.query(UserCurriculum).filter_by(user_id=p.id).order_by(UserCurriculum.order).all()
    return [{"date": (start + timedelta(weeks=r.week_start - 1)).isoformat(), "label": f"Weeks {r.week_start}–{r.week_end}", "items": [r.topic], "status": r.status} for r in rows]
