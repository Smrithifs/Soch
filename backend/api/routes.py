from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import AppState, InterviewSession, StudentProfile, UserCurriculum, UserPreferences, UserProblemHistory
from database.seed import create_profile, reset_demo
from services import agents, clock, executor, llm
from services import memory_model as mm
from services import learning_services as ls
from services import personalization_engine as pe
from services import tutor_engine
from services.knowledge import thinkmap_content
from services.problem_bank import PROBLEMS, get_problem, public_problem

router = APIRouter()
LANGS = {"Java": "java", "Python": "python", "java": "java", "python": "python"}


# ------------------------------------------------------------------ helpers
async def active(db: Session = Depends(get_db)) -> StudentProfile:
    st = db.query(AppState).first()
    p = db.get(StudentProfile, st.active_user_id) if st and st.active_user_id else None
    if not p:
        raise HTTPException(401, "No active profile — sign up or pick a profile")
    pr = db.query(UserPreferences).filter_by(user_id=p.id).first()
    clock.set_offset(pr.time_offset_days if pr and pr.time_offset_days else 0)
    return p


def prefs(db, p) -> UserPreferences:
    pr = db.query(UserPreferences).filter_by(user_id=p.id).first()
    if not pr:
        pr = UserPreferences(user_id=p.id, active_minutes=p.daily_minutes, editor_drafts={}, thinkmap={}, hint_levels={})
        db.add(pr)
        db.flush()
    return pr


def profile_dict(p: StudentProfile) -> dict:
    return {c.name: getattr(p, c.name) for c in p.__table__.columns if c.name != "created_at"} | {
        "track_label": pe.TRACK_LABEL[p.track], "days_left": pe.days_left(p), "virtual_date": clock.today().isoformat(),
        "time_offset_days": clock.offset()}


def check_slug(slug):
    if slug not in PROBLEMS:
        raise HTTPException(404, f"Unknown problem '{slug}'")


# ------------------------------------------------------------------ profiles
class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    track: Literal["oa", "interview", "learning"]
    level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    language: Literal["Java", "Python"] = "Java"
    daily_minutes: int = Field(ge=5, le=240)
    company: str | None = None
    role: str | None = None
    days_remaining: int | None = Field(default=None, ge=0, le=365)
    event_date: str | None = None
    questions_expected: int | None = Field(default=None, ge=1, le=6)
    weak_topics: list[str] = []
    revise_topics: list[str] = []
    starting_topic: str | None = None
    familiar_topics: list[str] = []
    goal: str | None = None
    months_available: int | None = Field(default=None, ge=1, le=24)

    @field_validator("name")
    @classmethod
    def strip(cls, v):
        return v.strip()


@router.get("/profiles")
def list_profiles(db: Session = Depends(get_db)):
    st = db.query(AppState).first()
    out = []
    for p in db.query(StudentProfile).order_by(StudentProfile.id).all():
        pr = db.query(UserPreferences).filter_by(user_id=p.id).first()
        clock.set_offset(pr.time_offset_days if pr and pr.time_offset_days else 0)
        out.append(profile_dict(p))
    clock.set_offset(0)
    return {"active_id": st.active_user_id if st else None, "profiles": out}


@router.post("/profiles")
def signup(body: ProfileIn, db: Session = Depends(get_db)):
    data = body.model_dump()
    if body.track == "oa" and not body.company:
        raise HTTPException(422, "Target company is required for OA")
    if body.track == "interview" and not (body.company and (body.days_remaining is not None or body.event_date)):
        raise HTTPException(422, "Company and interview date are required")
    if body.track == "learning" and not body.starting_topic:
        raise HTTPException(422, "Starting topic is required")
    data = {k: v for k, v in data.items() if v is not None}
    p = create_profile(db, data)
    return {"profile": profile_dict(p), "plan": pe.get_today(db, p)}


@router.get("/profiles/active")
def get_active(p: StudentProfile = Depends(active)):
    return profile_dict(p)


@router.get("/profiles/active/full")
def get_active_full(p: StudentProfile = Depends(active)):
    return profile_dict(p)


class SwitchIn(BaseModel):
    user_id: int


@router.post("/profiles/active")
def switch(body: SwitchIn, db: Session = Depends(get_db)):
    if not db.get(StudentProfile, body.user_id):
        raise HTTPException(404, "Profile not found")
    st = db.query(AppState).first() or AppState(id=1)
    st.active_user_id = body.user_id
    db.merge(st)
    db.commit()
    return {"ok": True}


@router.post("/logout")
def logout(db: Session = Depends(get_db)):
    st = db.query(AppState).first()
    if st:
        st.active_user_id = None
        db.commit()
    return {"ok": True}


class SettingsIn(BaseModel):
    daily_minutes: int | None = Field(default=None, ge=5, le=240)
    language: Literal["Java", "Python"] | None = None
    level: Literal["Beginner", "Intermediate", "Advanced"] | None = None


@router.put("/profiles/active")
def update_settings(body: SettingsIn, p=Depends(active), db: Session = Depends(get_db)):
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    if body.daily_minutes:
        prefs(db, p).active_minutes = body.daily_minutes
    db.commit()
    pe.generate_daily_schedule(db, p)
    return profile_dict(p)


# ------------------------------------------------------------------ plan
@router.get("/dashboard")
def dashboard(p=Depends(active), db: Session = Depends(get_db)):
    plan = pe.get_today(db, p)
    cur = db.query(UserCurriculum).filter_by(user_id=p.id).order_by(UserCurriculum.order).all()
    last_iv = db.query(InterviewSession).filter_by(user_id=p.id, status="complete", is_baseline=False).order_by(InterviewSession.id.desc()).first()
    return {"profile": profile_dict(p), "plan": plan, "progress": pe.preparation_progress(db, p), "next_problem": pe.next_problem(db, p),
            "calendar": pe.multi_day_plan(db, p), "curriculum": [_cur(c) for c in cur], "revisions": ls.list_revisions(db, p)[:8],
            "mistakes": ls.mistakes_view(db, p), "last_interview": last_iv.report if last_iv else None}


def _cur(c):
    return {"topic": c.topic, "order": c.order, "mastery": round(c.mastery * 100), "status": c.status, "prerequisites": c.prerequisites,
            "week_start": c.week_start, "week_end": c.week_end}


@router.get("/plan/today")
def plan_today(p=Depends(active), db: Session = Depends(get_db)):
    return pe.get_today(db, p)


@router.post("/plan/generate")
def plan_generate(p=Depends(active), db: Session = Depends(get_db)):
    return pe.generate_daily_schedule(db, p)


class TimeIn(BaseModel):
    minutes: int = Field(ge=1, le=240)


@router.put("/plan/time")
def plan_time(body: TimeIn, p=Depends(active), db: Session = Depends(get_db)):
    prefs(db, p).active_minutes = body.minutes
    db.commit()
    return pe.generate_daily_schedule(db, p, body.minutes)


@router.post("/plan/tasks/{task_id}/done")
def task_done(task_id: int, p=Depends(active), db: Session = Depends(get_db)):
    from database.models import DailyTask
    t = db.query(DailyTask).filter_by(id=task_id, user_id=p.id).first()
    if not t:
        raise HTTPException(404, "Task not found")
    if not t.done:
        t.done = True
        pe.award(db, p, f"task_{t.kind}", 5, t.minutes, {"task": t.id})
    db.commit()
    return pe.get_today(db, p)


@router.get("/calendar")
def calendar(p=Depends(active), db: Session = Depends(get_db)):
    return {"days": pe.multi_day_plan(db, p), "today": pe.get_today(db, p)}


@router.get("/curriculum")
def curriculum(p=Depends(active), db: Session = Depends(get_db)):
    return [_cur(c) for c in db.query(UserCurriculum).filter_by(user_id=p.id).order_by(UserCurriculum.order).all()]


# ------------------------------------------------------------------ problems & execution
@router.get("/problems")
def problems(p=Depends(active), db: Session = Depends(get_db)):
    solved = {h.slug for h in db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit", status="Accepted")}
    planned = [t["ref"] for t in pe.get_today(db, p)["tasks"] if t["kind"] == "problem"]
    return [{"slug": s, "title": v["title"], "difficulty": v["difficulty"], "topics": v["topics"], "solved": s in solved, "planned": s in planned}
            for s, v in sorted(PROBLEMS.items(), key=lambda kv: (kv[0] not in planned, planned.index(kv[0]) if kv[0] in planned else 0))]


@router.get("/problems/{slug}")
def problem(slug: str, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(slug)
    pr = prefs(db, p)
    last = db.query(UserProblemHistory).filter_by(user_id=p.id, slug=slug, kind="submit").order_by(UserProblemHistory.id.desc()).first()
    return public_problem(slug) | {"draft": (pr.editor_drafts or {}).get(slug, {}), "hints_used": (pr.hint_levels or {}).get(slug, 0),
                                   "last_submission": last.result if last else None, "engine": executor.engine_name()}


class DraftIn(BaseModel):
    language: Literal["java", "python"]
    code: str = Field(max_length=50_000)


@router.put("/drafts/{slug}")
def save_draft(slug: str, body: DraftIn, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(slug)
    pr = prefs(db, p)
    d = dict(pr.editor_drafts or {})
    d[slug] = dict(d.get(slug, {})) | {body.language: body.code}
    pr.editor_drafts = d
    db.commit()
    return {"ok": True}


class RunIn(BaseModel):
    slug: str
    language: Literal["java", "python"]
    code: str = Field(min_length=1, max_length=50_000)
    stdin: str = Field(default="", max_length=10_000)


@router.post("/run")
def run(body: RunIn, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(body.slug)
    try:
        r = executor.run_code(body.slug, body.language, body.code, body.stdin or get_problem(body.slug)["tests"][0]["input"])
    except executor.ExecutionUnavailable as e:
        raise HTTPException(503, str(e))
    except Exception as e:  # Judge0 network errors etc. — surface, never fake
        raise HTTPException(502, f"Execution service error: {e}")
    ls.record_submission(db, p, body.slug, body.language, body.code, "run", r)
    return r


@router.post("/submit")
def submit(body: RunIn, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(body.slug)
    try:
        r = executor.submit_code(body.slug, body.language, body.code)
    except executor.ExecutionUnavailable as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"Execution service error: {e}")
    extra = ls.record_submission(db, p, body.slug, body.language, body.code, "submit", r)
    return r | extra


# ------------------------------------------------------------------ tutor
class TutorIn(BaseModel):
    slug: str
    question: str = Field(default="", max_length=1000)
    code: str = Field(default="", max_length=50_000)
    language: Literal["java", "python"] = "java"
    mode: str | None = None


@router.post("/tutor")
def tutor(body: TutorIn, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(body.slug)
    prefs(db, p)
    return agents.tutor(db, p, body.slug, body.question, body.code, body.language, body.mode)


# ------------------------------------------------------------------ revision & mistakes
@router.get("/revisions")
def revisions(p=Depends(active), db: Session = Depends(get_db)):
    return ls.list_revisions(db, p)


class AnswerIn(BaseModel):
    choice: int | None = None
    revealed: bool = False


@router.post("/revisions/{card_id}/answer")
def revision_answer(card_id: int, body: AnswerIn, p=Depends(active), db: Session = Depends(get_db)):
    try:
        return ls.answer_card(db, p, card_id, body.choice, body.revealed)
    except KeyError:
        raise HTTPException(404, "Card not found")


@router.get("/mistakes")
def mistakes(p=Depends(active), db: Session = Depends(get_db)):
    return ls.mistakes_view(db, p)


class MistakeIn(BaseModel):
    category: str
    slug: str
    title: str
    explanation: str = ""


@router.post("/mistakes")
def add_mistake(body: MistakeIn, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(body.slug)
    if body.category not in ls.DNA_GROUPS:
        raise HTTPException(422, f"category must be one of {list(ls.DNA_GROUPS)}")
    m = ls.record_mistake(db, p, body.category, body.slug, PROBLEMS[body.slug]["topics"][0], body.title, body.explanation, {}, source="manual")
    db.commit()
    return {"id": m.id}


# ------------------------------------------------------------------ thinkmap
@router.get("/thinkmap/{slug}")
def thinkmap(slug: str, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(slug)
    return {"nodes": thinkmap_content(slug, get_problem(slug)), "completed": (prefs(db, p).thinkmap or {}).get(slug, [])}


class ThinkIn(BaseModel):
    completed: list[str]


@router.put("/thinkmap/{slug}")
def thinkmap_save(slug: str, body: ThinkIn, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(slug)
    pr = prefs(db, p)
    tm = dict(pr.thinkmap or {})
    tm[slug] = body.completed
    pr.thinkmap = tm
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ interview
class StartIn(BaseModel):
    slug: str | None = None


@router.post("/interview/start")
def interview_start(body: StartIn, p=Depends(active), db: Session = Depends(get_db)):
    if body.slug:
        check_slug(body.slug)
    return ls.start_interview(db, p, body.slug)


@router.get("/interview")
def interview_latest(p=Depends(active), db: Session = Depends(get_db)):
    s = db.query(InterviewSession).filter_by(user_id=p.id, is_baseline=False).order_by(InterviewSession.id.desc()).first()
    return ls.interview_state(s) if s else None


class IAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)


@router.post("/interview/{sid}/answer")
def interview_answer(sid: int, body: IAnswer, p=Depends(active), db: Session = Depends(get_db)):
    try:
        return ls.answer_interview(db, p, sid, body.answer)
    except KeyError:
        raise HTTPException(404, "No active interview session")


class FeedbackIn(BaseModel):
    notes: str = Field(max_length=4000)


@router.post("/interview/{sid}/feedback")
def interview_feedback(sid: int, body: FeedbackIn, p=Depends(active), db: Session = Depends(get_db)):
    s = db.query(InterviewSession).filter_by(id=sid, user_id=p.id).first()
    if not s or not s.report:
        raise HTTPException(404, "Completed session not found")
    s.report = dict(s.report) | {"student_notes": body.notes}
    db.commit()
    return s.report


# ------------------------------------------------------------------ analytics, company, demo
@router.get("/analytics")
def analytics(p=Depends(active), db: Session = Depends(get_db)):
    return ls.analytics(db, p)


@router.post("/progress")
def progress(p=Depends(active), db: Session = Depends(get_db)):
    return pe.preparation_progress(db, p)


@router.get("/company")
def company(p=Depends(active), db: Session = Depends(get_db)):
    from services.features import company_view
    return company_view(db, p)


@router.get("/calendar/month")
def cal_month(year: int, month: int, p=Depends(active), db: Session = Depends(get_db)):
    from services.features import calendar_month
    if not 1 <= month <= 12:
        raise HTTPException(422, "month 1-12")
    return calendar_month(db, p, year, month)


@router.get("/calendar/day")
def cal_day(date: str, p=Depends(active), db: Session = Depends(get_db)):
    from services.features import day_detail
    try:
        return day_detail(db, p, date)
    except ValueError:
        raise HTTPException(422, "date must be YYYY-MM-DD")


class OAItem(BaseModel):
    slug: str
    code: str = Field(default="", max_length=50_000)


class OAFinish(BaseModel):
    items: list[OAItem] = Field(min_length=1, max_length=6)
    seconds_used: int = Field(ge=0, le=86400)


@router.post("/mockoa/finish")
def mockoa_finish(body: OAFinish, p=Depends(active), db: Session = Depends(get_db)):
    from services.features import mock_oa_finish
    for it in body.items:
        check_slug(it.slug)
    return mock_oa_finish(db, p, [it.model_dump() for it in body.items], body.seconds_used)


@router.post("/demo/reset")
def demo_reset():
    reset_demo()
    return {"ok": True}


# ------------------------------------------------------------------ time travel (demo)
class TravelIn(BaseModel):
    days: float = Field(ge=-365, le=365)


@router.post("/time/travel")
def time_travel(body: TravelIn, p=Depends(active), db: Session = Depends(get_db)):
    pr = prefs(db, p)
    pr.time_offset_days = max(0.0, (pr.time_offset_days or 0) + body.days)
    db.commit()
    clock.set_offset(pr.time_offset_days)
    pe.generate_daily_schedule(db, p)
    return {"offset_days": pr.time_offset_days, "virtual_date": clock.today().isoformat()}


@router.post("/time/reset")
def time_reset(p=Depends(active), db: Session = Depends(get_db)):
    prefs(db, p).time_offset_days = 0
    db.commit()
    clock.set_offset(0)
    pe.generate_daily_schedule(db, p)
    return {"offset_days": 0, "virtual_date": clock.today().isoformat()}


# ------------------------------------------------------------------ memory & agents
@router.get("/memory")
def memory(p=Depends(active), db: Session = Depends(get_db)):
    from database.models import ProgressRecord
    last = db.query(ProgressRecord).filter_by(user_id=p.id).order_by(ProgressRecord.created_at.desc()).first()
    away = round((clock.now() - last.created_at).total_seconds() / 86400, 1) if last else None
    snap = mm.snapshot(db, p.id)
    solved = {h.slug for h in db.query(UserProblemHistory).filter_by(user_id=p.id, kind="submit", status="Accepted")}
    for m in snap:
        m["rescue_problems"] = [{"slug": s, "title": PROBLEMS[s]["title"]} for s in solved if mm.norm(PROBLEMS[s]["topics"][0]) == m["topic"]]
    return {"topics": snap, "days_away": away, "virtual_date": clock.today().isoformat(), "offset_days": clock.offset(),
            "model": {"formula": "R = exp(-t / S)", "bands": {"strong": ">= 75%", "fading": "45-75%", "forgotten": "< 45%"}}}


@router.get("/agents/status")
def agents_status():
    return llm.status(force=True)


@router.get("/agents/runs")
def agent_runs(limit: int = 60, p=Depends(active), db: Session = Depends(get_db)):
    from database.models import AgentRun
    runs = db.query(AgentRun).filter_by(user_id=p.id).order_by(AgentRun.id.desc()).limit(min(limit, 200)).all()
    return [{"id": r.id, "agent": r.agent, "trigger": r.trigger, "observed": r.observed, "decision": r.decision, "source": r.source,
             "model": r.model, "latency_ms": r.latency_ms, "error": r.error, "at": r.created_at.isoformat()} for r in runs]


@router.get("/coach")
def coach(refresh: bool = False, p=Depends(active), db: Session = Depends(get_db)):
    return agents.coach_brief(db, p, refresh)


@router.post("/agents/catchup")
def catchup(p=Depends(active), db: Session = Depends(get_db)):
    return agents.catch_up(db, p)


class ApplyIn(BaseModel):
    tasks: list[dict]


@router.post("/agents/catchup/apply")
def catchup_apply(body: ApplyIn, p=Depends(active), db: Session = Depends(get_db)):
    for t in body.tasks:
        if t.get("kind") not in ("recall", "revision", "problem") or not t.get("ref"):
            raise HTTPException(422, "invalid task")
    return agents.apply_catch_up(db, p, body.tasks)


class RecallStart(BaseModel):
    slug: str


@router.post("/recall/start")
def recall_start(body: RecallStart, p=Depends(active), db: Session = Depends(get_db)):
    check_slug(body.slug)
    return agents.recall_start(db, p, body.slug)


@router.get("/recall/active")
def recall_active(slug: str, p=Depends(active), db: Session = Depends(get_db)):
    from database.models import AgentSession
    s = db.query(AgentSession).filter_by(user_id=p.id, kind="recall", slug=slug).order_by(AgentSession.id.desc()).first()
    return agents.recall_view(s) if s else None


@router.post("/recall/{sid}/reply")
def recall_reply(sid: int, body: IAnswer, p=Depends(active), db: Session = Depends(get_db)):
    try:
        return agents.recall_reply(db, p, sid, body.answer)
    except KeyError:
        raise HTTPException(404, "No active recall session")


@router.delete("/tutor/{slug}")
def tutor_clear(slug: str, p=Depends(active), db: Session = Depends(get_db)):
    from database.models import AgentSession
    db.query(AgentSession).filter_by(user_id=p.id, kind="tutor", slug=slug, status="active").update({"status": "closed"})
    db.commit()
    return {"ok": True}
