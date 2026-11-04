"""Stand-in for Ollama's HTTP API — ONLY for automated tests of the agent plumbing (no real model here).
Run: uvicorn tests.fake_ollama:app --port 11555   then   OLLAMA_URL=http://127.0.0.1:11555 SOCH_MODEL=fake ..."""
import json

from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/api/tags")
def tags():
    return {"models": [{"name": "fake:latest"}]}


@app.post("/api/chat")
async def chat(req: Request):
    b = await req.json()
    sys = b["messages"][0]["content"]
    user = b["messages"][-1]["content"]
    if "Recall Coach" in sys:
        ans = json.loads(user)["student_answer"]
        ok = len(ans.split()) >= 5 and "idk" not in ans.lower()
        out = {"reply": "Right — that's the key idea." if ok else "Smaller step: trace [2,1,1,2] by hand. At house 3, what are your two choices?",
               "passed": ok, "confidence": "high" if ok else "low"}
    elif "Catch-up Planner" in sys:
        d = json.loads(user)
        cands = sorted(d["candidates"], key=lambda c: (c["kind"] != "recall", c.get("retention", 100)))
        tasks, total = [], 0
        for c in cands:
            if total + c["minutes"] <= d["analysis"]["minutes_available"]:
                tasks.append({"id": c["id"], "reason": f"{c['topic']} at {c.get('retention', '?')}% — fix first."})
                total += c["minutes"]
        out = {"message": f"You were away {d['analysis']['days_away']} days; recall first.", "tasks": tasks + [{"id": "bogus:id", "reason": "x"}]}
    elif "interviewer" in sys:
        out = {"score": 8, "feedback": "Clear and correct.", "follow_up": "What if prices can be negative?"}
    elif "coach" in sys:
        return {"message": {"role": "assistant", "content": "FAKE-LLM coach brief."}}
    else:
        return {"message": {"role": "assistant", "content": "FAKE-LLM tutor: " + user[:60]}}
    return {"message": {"role": "assistant", "content": json.dumps(out)}}
