"""End-to-end test of the three demo flows against the real API, real SQLite and real Java execution.
Run:  cd backend && python -m pytest -q tests   (or: python tests/test_demo_flow.py)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from services.problem_bank import DEMO_SNIPPETS as S  # noqa: E402

BUGGY = S["valid-parentheses"]["Counter approach (buggy)"]
STACK = S["valid-parentheses"]["Stack solution"]


def client():
    c = TestClient(app)
    c.__enter__()
    c.post("/api/demo/reset")
    return c


def switch(c, name):
    pid = next(p["id"] for p in c.get("/api/profiles").json()["profiles"] if p["name"] == name)
    c.post("/api/profiles/active", json={"user_id": pid})
    return pid


def kinds(plan):
    return [(t["kind"], t["ref"]) for t in plan["tasks"]]


def test_smrithi():
    c = client()
    r = c.post("/api/profiles", json=dict(name="Smrithi", track="oa", company="Zscaler", days_remaining=7, questions_expected=2,
                                          level="Beginner", language="Java", daily_minutes=25)).json()
    k = kinds(r["plan"])
    assert k[0] == ("problem", "valid-parentheses") and k[1] == ("problem", "maximum-subarray")
    assert [x for x in k if x[0] == "revision"] and len(k) == 3 and r["plan"]["total_minutes"] == 25
    sub = c.post("/api/submit", json={"slug": "valid-parentheses", "language": "java", "code": BUGGY}).json()
    assert sub["status"] == "Wrong Answer"
    ff = sub["first_failure"]
    assert ff["input"] == "(]" and ff["expected"] == "false" and ff["actual"] == "true"
    assert sub["analysis"]["category"] == "Logic Error"
    t = c.post("/api/tutor", json={"slug": "valid-parentheses", "question": "Why is my code failing?", "code": BUGGY}).json()
    assert "type or order" in t["body"] and "(]" in t["body"]
    t = c.post("/api/tutor", json={"slug": "valid-parentheses", "question": "Why do we need a stack here?", "code": BUGGY}).json()
    assert "LIFO" in t["body"]
    assert c.post("/api/tutor", json={"slug": "valid-parentheses", "question": "Can this be solved without a stack?", "code": STACK}).json()["intent"] == "alternatives"
    ok = c.post("/api/submit", json={"slug": "valid-parentheses", "language": "java", "code": STACK}).json()
    assert ok["status"] == "Accepted" and ok["passed"] == ok["total"]
    cx = c.post("/api/tutor", json={"slug": "valid-parentheses", "question": "What is the time and space complexity?", "code": STACK}).json()
    assert "O(n)" in cx["body"]
    assert c.post("/api/tutor", json={"slug": "valid-parentheses", "question": "Explain my code line by line", "code": STACK}).json()["intent"] == "explain_code"
    ms = c.post("/api/submit", json={"slug": "maximum-subarray", "language": "java", "code": S["maximum-subarray"]["Kadane's algorithm"]}).json()
    assert ms["status"] == "Accepted"
    for q, intent in [("Explain the logic of current = Math.max(nums[i], current + nums[i])", "kadane_line"),
                      ("How does it handle all-negative arrays?", "all_negative"), ("Why is it better than checking all subarrays?", "brute")]:
        assert c.post("/api/tutor", json={"slug": "maximum-subarray", "question": q, "code": ""}).json()["intent"] == intent
    sp = c.post("/api/tutor", json={"slug": "maximum-subarray", "question": "What is the space complexity?", "code": S["maximum-subarray"]["Kadane's algorithm"]}).json()
    assert "O(1)" in sp["body"]
    card = c.get("/api/revisions").json()[0]
    from services.knowledge import CARDS
    res = c.post(f"/api/revisions/{card['id']}/answer", json={"choice": CARDS[card["key"]]["correct"]}).json()
    assert res["correct"]
    d = c.get("/api/dashboard").json()
    assert d["profile"]["xp"] > 0 and d["profile"]["streak"] == 1 and d["progress"]["readiness"] > 50
    dna = c.get("/api/mistakes").json()
    assert any(m["category"] == "Logic Error" and m["slug"] == "valid-parentheses" for m in dna["mistakes"])


def test_dhanya():
    c = client()
    r = c.post("/api/profiles", json=dict(name="Dhanya", track="learning", goal="Prepare for DSA next year", starting_topic="Hashing",
                                          months_available=6, level="Beginner", language="Java", daily_minutes=15, familiar_topics=["Arrays"])).json()
    k = kinds(r["plan"])
    assert k[0] == ("problem", "two-sum") and len([x for x in k if x[0] == "revision"]) == 3
    topics = {t["title"].split(" revision")[0] for t in r["plan"]["tasks"][1:]}
    assert topics == {"Arrays", "Hashing", "Time Complexity"}
    cur = c.get("/api/curriculum").json()
    assert len(cur) == 14 and next(x for x in cur if x["topic"] == "Hashing")["status"] == "current"
    assert c.post("/api/submit", json={"slug": "two-sum", "language": "java", "code": S["two-sum"]["HashMap solution"]}).json()["status"] == "Accepted"
    assert "value → index" in c.post("/api/tutor", json={"slug": "two-sum", "question": "Why did you use a HashMap?", "code": S["two-sum"]["HashMap solution"]}).json()["body"]
    tc = c.post("/api/tutor", json={"slug": "two-sum", "question": "What is the time complexity?", "code": S["two-sum"]["HashMap solution"]}).json()
    assert "Time: O(n)" in tc["body"] and "Space: O(n)" in tc["body"]
    assert c.post("/api/tutor", json={"slug": "two-sum", "question": "What happens with duplicate numbers like [3,3]?"}).json()["intent"] == "duplicates"
    h1 = c.post("/api/tutor", json={"slug": "two-sum", "question": "Give me a hint without revealing the solution"}).json()
    h2 = c.post("/api/tutor", json={"slug": "two-sum", "question": "another hint please"}).json()
    assert h1["title"] != h2["title"]
    p10 = c.put("/api/plan/time", json={"minutes": 10}).json()
    assert kinds(p10)[0] == ("problem", "two-sum") and len(p10["tasks"]) == 2
    p5 = c.put("/api/plan/time", json={"minutes": 5}).json()
    assert all(t["kind"] == "revision" for t in p5["tasks"]) and len(p5["tasks"]) == 3 and "revision only" in p5["rule"]
    card = next(x for x in c.get("/api/revisions").json() if x["topic"] == "Hashing")
    from services.knowledge import CARDS
    wrong = (CARDS[card["key"]]["correct"] + 1) % 4
    res = c.post(f"/api/revisions/{card['id']}/answer", json={"choice": wrong}).json()
    assert not res["correct"] and res["next_due_in"] == "10 minutes"
    dna = c.get("/api/mistakes").json()
    assert any(m["category"] == "Concept Recall Error" and m["topic"] == "Hashing" for m in dna["mistakes"])
    assert c.get("/api/revisions").json()[0]["key"] == card["key"]  # missed card jumps to the front


def test_vismaya():
    c = client()
    r = c.post("/api/profiles", json=dict(name="Vismaya", track="interview", company="Microsoft", role="Software Engineering Internship",
                                          days_remaining=3, level="Beginner", language="Java", revise_topics=["Arrays", "Hashing", "Stacks"],
                                          daily_minutes=20)).json()
    k = kinds(r["plan"])
    assert k[0] == ("problem", "best-time-to-buy-and-sell-stock")
    assert len([x for x in k if x[0] == "revision"]) == 6 and k[-1][0] == "communication"
    cal = c.get("/api/calendar").json()["days"]
    assert cal[0]["items"][1] == "Best Time to Buy and Sell Stock" and cal[2]["items"][-1] == "Mock interview"
    code = S["best-time-to-buy-and-sell-stock"]["Running minimum"]
    assert c.post("/api/submit", json={"slug": "best-time-to-buy-and-sell-stock", "language": "java", "code": code}).json()["status"] == "Accepted"
    for q, intent in [("Why do you track the lowest price?", "why_ds"), ("What happens if prices only decrease?", "decreasing"),
                      ("Explain the approach in one sentence as in an interview", "one_liner"), ("What edge cases should be handled?", "edge_cases")]:
        assert c.post("/api/tutor", json={"slug": "best-time-to-buy-and-sell-stock", "question": q, "code": code}).json()["intent"] == intent
    s = c.post("/api/interview/start", json={}).json()
    assert s["slug"] == "best-time-to-buy-and-sell-stock"
    answers = [
        "We get daily prices and must buy once then sell on a later day to maximise the profit difference, returning 0 if no profit.",
        "Scan once in a single pass, tracking the minimum price so far and the best profit difference.",
        "Brute force checks every pair of buy and sell days with nested loops, which is O(n^2).",
        "Instead of rescanning, keep the running min price so far, so each day is O(1).",
        "No data structure needed, just two integer variables, constant memory.",
        "Time is O(n) because it is one pass with constant work per day.",
        "Space is O(1), constant, only two variables.",
        "Strictly decreasing prices return 0, a single day returns 0, and all equal prices give zero profit.",
        "done",
        "I scan once keeping the lowest price so far, so each day I compute the profit in O(1), which gives O(n) time and O(1) space.",
    ]
    for a in answers:
        s = c.post(f"/api/interview/{s['id']}/answer", json={"answer": a}).json()
    rep = s["report"]
    assert s["status"] == "complete" and rep["overall"] >= 8 and rep["scores"]["Code correctness"] == 10
    assert rep["improvement_vs_baseline"]["Time complexity"] > 0
    dna = c.get("/api/mistakes").json()["mistakes"]
    assert any(m["group"] == "communication" and m["status"] in ("improving", "resolved") for m in dna)
    assert any(m["group"] == "complexity" and m["status"] in ("improving", "resolved") for m in dna)


def test_isolation_and_logout():
    c = client()
    switch(c, "Smrithi")
    c.post("/api/submit", json={"slug": "valid-parentheses", "language": "java", "code": BUGGY})
    switch(c, "Dhanya")
    assert not c.get("/api/mistakes").json()["mistakes"]
    assert c.get("/api/dashboard").json()["profile"]["xp"] == 0
    c.post("/api/logout")
    assert c.get("/api/dashboard").status_code == 401


def test_compile_error_is_real():
    c = client()
    switch(c, "Smrithi")
    r = c.post("/api/submit", json={"slug": "valid-parentheses", "language": "java", "code": "class Solution { public boolean isValid(String s) { return x } }"}).json()
    assert r["status"] == "Compilation Error" and "error" in r["stderr"].lower() and r["analysis"]["category"] == "Syntax Error"
    r = c.post("/api/run", json={"slug": "valid-parentheses", "language": "python", "code": "class Solution:\n    def isValid(self, s):\n        return len(s) % 2 == 0\n", "stdin": "(]"}).json()
    assert r["status"] == "Executed" and r["stdout"].strip() == "true"


if __name__ == "__main__":
    for f in [test_smrithi, test_dhanya, test_vismaya, test_isolation_and_logout, test_compile_error_is_real]:
        f()
        print("PASS", f.__name__)
