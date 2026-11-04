from datetime import date, timedelta

from .db import Base, SessionLocal, engine
from .models import AppState, InterviewSession, MistakeRecord, Problem, StudentProfile, UserPreferences
from services import clock

DEMO_PROFILES = [
    dict(name="Smrithi", track="oa", company="Zscaler", days_remaining=7, questions_expected=2, level="Beginner", language="Java",
         daily_minutes=25, weak_topics=[]),
    dict(name="Dhanya", track="learning", goal="Prepare for DSA next year", starting_topic="Hashing", months_available=6, level="Beginner",
         language="Java", daily_minutes=15, familiar_topics=["Arrays"]),
    dict(name="Vismaya", track="interview", company="Microsoft", role="Software Engineering Internship", days_remaining=3, level="Beginner",
         language="Java", revise_topics=["Arrays", "Hashing", "Stacks"], daily_minutes=20),
]


def create_profile(db, data: dict, is_demo=False) -> StudentProfile:
    from services import personalization_engine as pe
    data = dict(data)
    if data.get("days_remaining") is not None and not data.get("event_date"):
        data["event_date"] = (clock.today() + timedelta(days=int(data["days_remaining"]))).isoformat()
    if data.get("event_date") and data.get("days_remaining") is None:
        data["days_remaining"] = max(0, (date.fromisoformat(data["event_date"]) - clock.today()).days)
    existing = db.query(StudentProfile).filter(StudentProfile.name.ilike(data["name"])).first()
    if existing:  # re-onboarding the same name updates that profile instead of duplicating it
        for k, v in data.items():
            setattr(existing, k, v)
        p = existing
    else:
        p = StudentProfile(is_demo=is_demo, **data)
        db.add(p)
        db.flush()
        db.add(UserPreferences(user_id=p.id, active_minutes=p.daily_minutes, editor_drafts={}, thinkmap={}, hint_levels={}))
    pref = db.query(UserPreferences).filter_by(user_id=p.id).first()
    if pref:
        pref.active_minutes = p.daily_minutes
    pe.build_curriculum(db, p)
    _seed_familiar_memory(db, p)
    pe.ensure_cards(db, p)
    db.flush()
    if p.name.lower() == "vismaya" and is_demo:
        _vismaya_baseline(db, p)
    pe.generate_daily_schedule(db, p, p.daily_minutes)
    st = db.query(AppState).first() or AppState(id=1)
    st.active_user_id = p.id
    db.merge(st)
    db.commit()
    return p


def _seed_familiar_memory(db, p):
    """Topics the student says they already know start with moderate stability (learned a few days ago)."""
    from datetime import timedelta
    from .models import TopicMemory
    from services.memory_model import norm
    for t in p.familiar_topics or []:
        t = norm(t)
        if not db.query(TopicMemory).filter_by(user_id=p.id, topic=t).first():
            db.add(TopicMemory(user_id=p.id, topic=t, stability=6.0, last_review=clock.now() - timedelta(days=2), reviews=2, lapses=0,
                               history=[{"at": (clock.now() - timedelta(days=2)).isoformat(), "q": "strong", "S": 6.0, "src": "self-reported familiar"}]))


def _vismaya_baseline(db, p):
    """Labelled demo baseline (pre-platform self-assessment) so improvement can be shown. Not an execution result."""
    db.add(InterviewSession(user_id=p.id, slug="two-sum", step=10, status="complete", is_baseline=True, answers=[],
                            scores={"Time complexity": 4, "Space complexity": 3, "Communication": 4},
                            report={"overall": 4.5, "summary": "Seeded demo baseline: self-assessment before using SOCH."}))
    db.add(MistakeRecord(user_id=p.id, category="Complexity Error", dna_group="complexity", slug="two-sum", topic="Hashing",
                         title="Baseline: unsure how to justify O(n) vs O(n²)", source="seed-baseline", status="open",
                         explanation="Self-assessed baseline: could name Big-O but not justify it (passes × work per element). Seeded for the demo.",
                         evidence={"baseline_score": 4}, revision_card="complexity_single", next_problem="best-time-to-buy-and-sell-stock"))
    db.add(MistakeRecord(user_id=p.id, category="Communication Issue", dna_group="communication", slug="two-sum", topic="Hashing",
                         title="Baseline: explanations too short, no structure", source="seed-baseline", status="open",
                         explanation="Self-assessed baseline: answers jumped to code without stating the approach. Seeded for the demo.",
                         evidence={"baseline_score": 4}, revision_card="hashmap_store", next_problem="best-time-to-buy-and-sell-stock"))


def seed_problems(db):
    from services.problem_bank import PROBLEMS
    for slug, p in PROBLEMS.items():
        db.merge(Problem(slug=slug, title=p["title"], difficulty=p["difficulty"], topics=p["topics"]))


def seed_if_empty():
    db = SessionLocal()
    try:
        seed_problems(db)
        db.commit()
        if not db.query(StudentProfile).count():
            for d in DEMO_PROFILES:
                create_profile(db, d, is_demo=True)
            st = db.query(AppState).first()
            st.active_user_id = db.query(StudentProfile).filter_by(name="Smrithi").first().id
            db.commit()
    finally:
        db.close()


def reset_demo():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed_if_empty()
