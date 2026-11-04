"""Forgetting + agents end-to-end. Real Java execution, real SQLite.
LLM path: start tests/fake_ollama.py on :11555 and run with OLLAMA_URL=http://127.0.0.1:11555 SOCH_MODEL=fake
Offline path: run with SOCH_LLM=off — agents must still work (fallback) and say so."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from services.problem_bank import DEMO_SNIPPETS as S  # noqa: E402

LLM_ON = os.getenv("SOCH_LLM") != "off"
EXPECT = "llm" if LLM_ON else "fallback"


def setup(name):
    c = TestClient(app)
    c.__enter__()
    c.post("/api/demo/reset")
    pid = next(p["id"] for p in c.get("/api/profiles").json()["profiles"] if p["name"] == name)
    c.post("/api/profiles/active", json={"user_id": pid})
    return c


def topic(c, t):
    return next((m for m in c.get("/api/memory").json()["topics"] if m["topic"] == t), None)


def test_dp_yesterday_blank_today():
    c = setup("Dhanya")
    assert c.get("/api/agents/status").json()["online"] == LLM_ON
    bad = c.post("/api/submit", json={"slug": "house-robber", "language": "java", "code": S["house-robber"]["Greedy every-other (buggy)"]}).json()
    assert bad["status"] == "Wrong Answer" and bad["first_failure"]["input"] == "2,1,1,2"
    ok = c.post("/api/submit", json={"slug": "house-robber", "language": "java", "code": S["house-robber"]["DP take/skip"]}).json()
    assert ok["status"] == "Accepted"
    dp = topic(c, "Dynamic Programming")
    assert dp["retention"] == 100 and dp["status"] == "strong"
    # --- next day
    c.post("/api/time/travel", json={"days": 1})
    dp = topic(c, "Dynamic Programming")
    assert 35 <= dp["retention"] <= 50 and dp["status"] == "forgotten", dp
    plan = c.get("/api/plan/today").json()
    assert plan["tasks"][0]["kind"] == "recall" and plan["tasks"][0]["ref"] == "house-robber"
    # --- Recall Rescue ladder
    s = c.post("/api/recall/start", json={"slug": "house-robber"}).json()
    assert s["stage"] == 0 and "%" in s["messages"][0]["content"]
    s = c.post(f"/api/recall/{s['id']}/reply", json={"answer": "idk"}).json()
    assert s["stage"] == 0  # blank → smaller cue, no advance
    for a in ["Max money from non adjacent houses, input array output a number",
              "Choices at each house overlap with earlier choices so it is DP not greedy",
              "dp of i is the best total using houses zero to i",
              "dp i equals max of dp i minus 1 and dp i minus 2 plus nums i",
              "base dp0 is nums0 and dp1 is max of first two, fill left to right"]:
        s = c.post(f"/api/recall/{s['id']}/reply", json={"answer": a}).json()
    assert s["stage"] == 5
    s = c.post(f"/api/recall/{s['id']}/reply", json={"answer": "done"}).json()
    assert s["stage"] == 5 and s["status"] == "active" and "don't see" in s["messages"][-1]["content"]  # no real submit since start → not trusted
    assert c.post("/api/submit", json={"slug": "house-robber", "language": "java", "code": S["house-robber"]["DP take/skip"]}).json()["status"] == "Accepted"
    s = c.post(f"/api/recall/{s['id']}/reply", json={"answer": "done"}).json()
    assert s["status"] == "complete"
    dp2 = topic(c, "Dynamic Programming")
    assert dp2["stability_days"] > dp["stability_days"] * 1.5 and dp2["retention"] == 100
    runs = c.get("/api/agents/runs").json()
    assert any(r["agent"] == "Recall Coach" and r["source"] == EXPECT for r in runs)


def test_skip_ten_days_catch_up():
    c = setup("Smrithi")
    for slug, snip in [("valid-parentheses", "Stack solution"), ("maximum-subarray", "Kadane's algorithm")]:
        assert c.post("/api/submit", json={"slug": slug, "language": "java", "code": S[slug][snip]}).json()["status"] == "Accepted"
    c.post("/api/time/travel", json={"days": 10})
    mem = c.get("/api/memory").json()
    assert mem["days_away"] >= 10 and all(m["status"] == "forgotten" for m in mem["topics"])
    assert c.get("/api/dashboard").json()["profile"]["days_left"] == 0  # OA date has passed in virtual time
    plan = c.post("/api/agents/catchup").json()
    assert plan["source"] == EXPECT and plan["tasks"][0]["kind"] == "recall"
    assert plan["total_minutes"] <= 25 and all(":" in t["id"] and not t["id"].startswith("bogus") for t in plan["tasks"])
    today = c.post("/api/agents/catchup/apply", json={"tasks": plan["tasks"]}).json()
    assert today["tasks"][0]["kind"] == "recall"
    c.post("/api/time/reset")
    assert c.get("/api/memory").json()["offset_days"] == 0


def test_tutor_and_interview_agents():
    c = setup("Vismaya")
    code = S["best-time-to-buy-and-sell-stock"]["Running minimum"]
    t = c.post("/api/tutor", json={"slug": "best-time-to-buy-and-sell-stock", "question": "why track the min?", "code": code}).json()
    assert t["source"] == EXPECT and t["body"]
    c.post("/api/submit", json={"slug": "best-time-to-buy-and-sell-stock", "language": "java", "code": code})
    s = c.post("/api/interview/start", json={}).json()
    s = c.post(f"/api/interview/{s['id']}/answer", json={"answer": "We buy once and sell later to maximise profit."}).json()
    assert s["answers"][0]["graded_by"] == ("llm" if LLM_ON else "rubric")
    b = c.get("/api/coach?refresh=true").json()
    assert b["source"] == EXPECT and b["text"]


if __name__ == "__main__":
    for f in [test_dp_yesterday_blank_today, test_skip_ten_days_catch_up, test_tutor_and_interview_agents]:
        f()
        print("PASS", f.__name__, f"({EXPECT})")
