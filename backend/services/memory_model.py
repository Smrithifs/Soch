"""Forgetting-curve memory model (per student, per topic).

Retention  R(t) = exp(-t / S)        t = days since last successful review, S = stability (days)
After a review, stability changes by the spacing effect: reviewing something you had partly
forgotten (low R) strengthens it more than cramming it again while it's fresh.

    strong  (solved unaided / recalled correctly):  S ← S · (1.5 + 2·(1 − R))
    weak    (solved with hints / recall needed help): S ← S · 1.2
    fail    (could not recall / wrong):               S ← max(0.3, S · 0.5)
A brand-new topic starts at S = 1.2 days, so one day later retention is ≈ 43% — the
"I solved DP yesterday and today I'm blank" effect.
"""
import math
from datetime import timedelta

from sqlalchemy.orm import Session

from database.models import TopicMemory
from . import clock
from .knowledge import TOPIC_ALIASES

FIRST_S = {"strong": 1.2, "weak": 0.8, "fail": 0.4}
STRONG, FADING = 0.75, 0.45


def norm(t: str) -> str:
    return TOPIC_ALIASES.get(t, t)


def retention(m: TopicMemory, at=None) -> float:
    if not m.last_review:
        return 0.0
    days = max(0.0, ((at or clock.now()) - m.last_review).total_seconds() / 86400)
    return math.exp(-days / max(m.stability, 0.1))


def status(r: float) -> str:
    return "strong" if r >= STRONG else "fading" if r >= FADING else "forgotten"


def reinforce(db: Session, uid: int, topic: str, quality: str, source: str = "") -> TopicMemory:
    topic = norm(topic)
    m = db.query(TopicMemory).filter_by(user_id=uid, topic=topic).first()
    if not m:
        if quality == "fail":  # failing something never learned isn't forgetting
            m = TopicMemory(user_id=uid, topic=topic, stability=FIRST_S["fail"], last_review=None, reviews=0, lapses=1, history=[])
            db.add(m)
            db.flush()
            return m
        m = TopicMemory(user_id=uid, topic=topic, stability=FIRST_S[quality], last_review=clock.now(), reviews=1, lapses=0,
                        history=[{"at": clock.now().isoformat(), "q": quality, "R": None, "S": FIRST_S[quality], "src": source}])
        db.add(m)
        db.flush()
        return m
    r = retention(m) if m.last_review else 0.0
    if quality in ("strong", "weak") and m.last_review and (clock.now() - m.last_review).total_seconds() < 4 * 3600:
        return m  # re-solving within the same sitting isn't spaced practice
    if quality == "strong":
        m.stability = round(m.stability * (1.5 + 2 * (1 - r)), 3)
        m.last_review = clock.now()
    elif quality == "weak":
        m.stability = round(m.stability * 1.2, 3)
        m.last_review = clock.now()
    else:
        m.stability = round(max(0.3, m.stability * 0.5), 3)
        m.lapses = (m.lapses or 0) + 1
        if m.last_review:
            m.last_review = clock.now() - timedelta(days=m.stability * 0.7)  # a lapse leaves the memory weak, not reset
    m.reviews = (m.reviews or 0) + 1
    m.history = list(m.history or []) + [{"at": clock.now().isoformat(), "q": quality, "R": round(r, 2), "S": m.stability, "src": source}]
    db.flush()
    return m


def snapshot(db: Session, uid: int) -> list[dict]:
    out = []
    for m in db.query(TopicMemory).filter_by(user_id=uid).all():
        if not m.last_review:
            continue
        r = retention(m)
        days = (clock.now() - m.last_review).total_seconds() / 86400
        proj = [{"day": d, "retention": round(100 * math.exp(-(days + d) / m.stability))} for d in (0, 1, 2, 3, 5, 7, 10, 14, 21, 30)]
        # days until it drops below the 'fading' and 'forgotten' lines
        t_fade = max(0.0, -m.stability * math.log(STRONG) - days)
        t_forget = max(0.0, -m.stability * math.log(FADING) - days)
        out.append({"topic": m.topic, "retention": round(r * 100), "status": status(r), "stability_days": round(m.stability, 2),
                    "days_since": round(days, 1), "reviews": m.reviews, "lapses": m.lapses, "projection": proj,
                    "fades_in_days": round(t_fade, 1), "forgotten_in_days": round(t_forget, 1), "history": (m.history or [])[-6:]})
    return sorted(out, key=lambda x: x["retention"])


def topic_retention(db: Session, uid: int, topic: str) -> float | None:
    m = db.query(TopicMemory).filter_by(user_id=uid, topic=norm(topic)).first()
    return retention(m) if m and m.last_review else None
