from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from .db import Base


def now():
    from services import clock
    return clock.now()


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    track = Column(String(20), nullable=False)  # oa | interview | learning
    level = Column(String(20), default="Beginner")
    language = Column(String(20), default="Java")
    daily_minutes = Column(Integer, default=20)
    company = Column(String(80))
    role = Column(String(120))
    days_remaining = Column(Integer)          # OA / interview countdown
    event_date = Column(String(20))
    questions_expected = Column(Integer)
    weak_topics = Column(JSON, default=list)
    revise_topics = Column(JSON, default=list)
    starting_topic = Column(String(60))
    familiar_topics = Column(JSON, default=list)
    goal = Column(String(200))
    months_available = Column(Integer)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_active = Column(String(20))
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), unique=True)
    active_minutes = Column(Integer)  # today's chosen time (time selector)
    editor_drafts = Column(JSON, default=dict)   # autosave: {slug: {lang: code}}
    thinkmap = Column(JSON, default=dict)        # {slug: [completed node ids]}
    hint_levels = Column(JSON, default=dict)     # {slug: hints revealed}
    time_offset_days = Column(Float, default=0)  # demo time travel


class AppState(Base):
    __tablename__ = "app_state"
    id = Column(Integer, primary_key=True)
    active_user_id = Column(Integer)


class Problem(Base):
    __tablename__ = "problems"
    slug = Column(String(80), primary_key=True)
    title = Column(String(120))
    difficulty = Column(String(20))
    topics = Column(JSON)


class UserProblemHistory(Base):
    __tablename__ = "user_problem_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    slug = Column(String(80))
    kind = Column(String(10))  # run | submit
    language = Column(String(20))
    code = Column(Text)
    status = Column(String(40))
    passed = Column(Integer, default=0)
    total = Column(Integer, default=0)
    result = Column(JSON)
    hints_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)


class UserCurriculum(Base):
    __tablename__ = "user_curriculum"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    topic = Column(String(60))
    order = Column(Integer)
    mastery = Column(Float, default=0.0)  # 0..1
    status = Column(String(20), default="locked")  # locked | current | done | revise
    prerequisites = Column(JSON, default=list)
    week_start = Column(Integer)
    week_end = Column(Integer)


class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    day = Column(String(20))
    position = Column(Integer)
    kind = Column(String(20))  # problem | revision | communication | mock
    ref = Column(String(80))   # problem slug or card id
    title = Column(String(160))
    minutes = Column(Float)
    reason = Column(Text)
    done = Column(Boolean, default=False)


class RevisionCard(Base):
    __tablename__ = "revision_cards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    card_key = Column(String(60))
    topic = Column(String(60))
    concept = Column(String(80))
    interval_days = Column(Float, default=0)
    correct_streak = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    correct = Column(Integer, default=0)
    due_at = Column(DateTime, default=now)
    last_reviewed = Column(DateTime)
    last_result = Column(String(10))


class MistakeRecord(Base):
    __tablename__ = "mistake_records"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    category = Column(String(40))        # Logic Error, Concept Recall Error, ...
    dna_group = Column(String(40))       # conceptual | pattern | logic | implementation | complexity | edge | communication
    slug = Column(String(80))
    topic = Column(String(60))
    title = Column(String(200))
    explanation = Column(Text)
    evidence = Column(JSON)
    revision_card = Column(String(60))
    next_problem = Column(String(80))
    status = Column(String(20), default="open")  # open | improving | resolved
    source = Column(String(30))          # execution | revision | interview | seed-baseline
    created_at = Column(DateTime, default=now)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    slug = Column(String(80))
    step = Column(Integer, default=0)
    answers = Column(JSON, default=list)
    scores = Column(JSON, default=dict)
    report = Column(JSON)
    status = Column(String(20), default="active")
    is_baseline = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)


class ProgressRecord(Base):
    __tablename__ = "progress_records"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    day = Column(String(20))
    event = Column(String(40))
    xp = Column(Integer, default=0)
    minutes = Column(Float, default=0)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now)


class TopicMemory(Base):
    __tablename__ = "topic_memory"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    topic = Column(String(60))
    stability = Column(Float, default=1.2)   # days
    last_review = Column(DateTime)
    reviews = Column(Integer, default=0)
    lapses = Column(Integer, default=0)
    history = Column(JSON, default=list)


class AgentRun(Base):
    """Trace of every agent decision — what it saw, what it decided, whether the LLM or the offline rules answered."""
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    agent = Column(String(40))
    trigger = Column(String(200))
    observed = Column(JSON)        # the context the agent was given
    decision = Column(JSON)        # structured output
    source = Column(String(20))    # llm | fallback
    model = Column(String(80))
    latency_ms = Column(Integer)
    error = Column(Text)
    created_at = Column(DateTime, default=now)


class AgentSession(Base):
    """Multi-turn conversations (tutor chat per problem, recall rescue)."""
    __tablename__ = "agent_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    kind = Column(String(20))      # tutor | recall
    slug = Column(String(80))
    stage = Column(Integer, default=0)
    messages = Column(JSON, default=list)
    status = Column(String(20), default="active")
    outcome = Column(String(20))
    created_at = Column(DateTime, default=now)
