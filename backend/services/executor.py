"""Real code execution. Two backends:

* Judge0 (set JUDGE0_URL, optionally JUDGE0_KEY for RapidAPI) — remote sandbox.
* Local sandbox (default) — javac/java or python3 in a temp dir with wall-clock timeout,
  heap cap, output cap and an isolated working directory.

Every status returned here comes from an actual compiler/process. Nothing is fabricated.
"""
import os
import re
import shutil
import subprocess
import tempfile
import time

import httpx

from .problem_bank import JAVA_DRIVERS, PYTHON_DRIVERS, get_problem

RUN_TIMEOUT = float(os.getenv("SOCH_RUN_TIMEOUT", "4"))
COMPILE_TIMEOUT = float(os.getenv("SOCH_COMPILE_TIMEOUT", "20"))
MAX_OUTPUT = 64_000
JUDGE0_URL = os.getenv("JUDGE0_URL", "").rstrip("/")
JUDGE0_KEY = os.getenv("JUDGE0_KEY", "")
JUDGE0_LANG = {"java": 62, "python": 71, "cpp": 54}


class ExecutionUnavailable(Exception):
    pass


def _clean_env():
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "HOME": tempfile.gettempdir()}
    if os.environ.get("JAVA_HOME"):
        env["JAVA_HOME"] = os.environ["JAVA_HOME"]
    return env


def _build_source(slug: str, language: str, code: str) -> str:
    if language == "java":
        if re.search(r"\bpublic\s+class\s+Main\b", code):
            return code  # user supplied their own Main (custom run)
        # a 'public class Solution' cannot live in Main.java — drop the modifier
        code = re.sub(r"\bpublic\s+class\s+Solution\b", "class Solution", code)
        return code + "\n" + JAVA_DRIVERS[slug]
    if language == "python":
        return code + "\n" + PYTHON_DRIVERS[slug]
    raise ValueError(f"Language '{language}' has no driver for this problem")


def _trunc(s: str) -> str:
    return s if len(s) <= MAX_OUTPUT else s[:MAX_OUTPUT] + "\n…[output truncated]"


# ---------------------------------------------------------------- local sandbox
class LocalSession:
    def __init__(self, slug, language, code):
        self.slug, self.language, self.code = slug, language, code
        self.dir = tempfile.mkdtemp(prefix="soch_")
        self.compile_error = None
        self.compile_ms = 0

    def __enter__(self):
        src = _build_source(self.slug, self.language, self.code)
        if self.language == "java":
            if not shutil.which("javac"):
                raise ExecutionUnavailable("javac not found. Install a JDK (e.g. `brew install openjdk@21`) or set JUDGE0_URL.")
            path = os.path.join(self.dir, "Main.java")
            open(path, "w").write(src)
            t = time.time()
            try:
                r = subprocess.run(["javac", "-J-Xmx512m", "-nowarn", "Main.java"], cwd=self.dir, capture_output=True,
                                   text=True, timeout=COMPILE_TIMEOUT, env=_clean_env())
            except subprocess.TimeoutExpired:
                self.compile_error = "Compilation timed out"
                return self
            self.compile_ms = int((time.time() - t) * 1000)
            if r.returncode != 0:
                self.compile_error = _trunc(_strip_java_noise(r.stderr or r.stdout))
        else:
            open(os.path.join(self.dir, "main.py"), "w").write(src)
            r = subprocess.run(["python3", "-I", "-m", "py_compile", "main.py"], cwd=self.dir, capture_output=True, text=True,
                               timeout=COMPILE_TIMEOUT, env=_clean_env())
            if r.returncode != 0:
                self.compile_error = _trunc(r.stderr)
        return self

    def run(self, stdin: str) -> dict:
        cmd = ["java", "-Xmx256m", "-Xss64m", "-XX:+UseSerialGC", "-XX:TieredStopAtLevel=1", "-cp", self.dir, "Main"] \
            if self.language == "java" else ["python3", "-I", "main.py"]
        t = time.time()
        try:
            r = subprocess.run(cmd, cwd=self.dir, input=stdin, capture_output=True, text=True, timeout=RUN_TIMEOUT,
                               env=_clean_env())
        except subprocess.TimeoutExpired as e:
            return {"status": "Time Limit Exceeded", "stdout": _trunc((e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")),
                    "stderr": f"Process killed after {RUN_TIMEOUT}s", "time_ms": int(RUN_TIMEOUT * 1000), "exit_code": None}
        ms = int((time.time() - t) * 1000)
        stderr = _strip_java_noise(r.stderr)
        status = "Runtime Error" if r.returncode != 0 else "OK"
        return {"status": status, "stdout": _trunc(r.stdout), "stderr": _trunc(stderr), "time_ms": ms, "exit_code": r.returncode}

    def __exit__(self, *a):
        shutil.rmtree(self.dir, ignore_errors=True)


def _strip_java_noise(s: str) -> str:
    return "\n".join(l for l in (s or "").splitlines() if not l.startswith("Picked up JAVA_TOOL_OPTIONS")).strip()


# ---------------------------------------------------------------- Judge0
def _judge0_run(slug, language, code, stdin) -> dict:
    headers = {"content-type": "application/json"}
    if JUDGE0_KEY:
        headers |= {"X-RapidAPI-Key": JUDGE0_KEY, "X-RapidAPI-Host": JUDGE0_URL.split("//")[-1]}
    body = {"source_code": _build_source(slug, language, code), "language_id": JUDGE0_LANG[language], "stdin": stdin,
            "cpu_time_limit": RUN_TIMEOUT, "memory_limit": 256000}
    r = httpx.post(f"{JUDGE0_URL}/submissions?base64_encoded=false&wait=true", json=body, headers=headers, timeout=60)
    r.raise_for_status()
    d = r.json()
    sid = (d.get("status") or {}).get("id")
    status = {3: "OK", 5: "Time Limit Exceeded", 6: "Compilation Error"}.get(sid, "Runtime Error" if sid and sid >= 7 else "OK")
    return {"status": status, "stdout": d.get("stdout") or "", "stderr": (d.get("stderr") or d.get("compile_output") or ""),
            "time_ms": int(float(d.get("time") or 0) * 1000), "exit_code": d.get("exit_code")}


# ---------------------------------------------------------------- public API
def engine_name() -> str:
    return "judge0" if JUDGE0_URL else "local-sandbox"


def run_code(slug: str, language: str, code: str, stdin: str) -> dict:
    if JUDGE0_URL:
        r = _judge0_run(slug, language, code, stdin)
        return r | {"engine": "judge0"}
    with LocalSession(slug, language, code) as s:
        if s.compile_error:
            return {"status": "Compilation Error", "stdout": "", "stderr": s.compile_error, "time_ms": s.compile_ms, "engine": "local-sandbox"}
        r = s.run(stdin)
        if r["status"] == "OK":
            r["status"] = "Executed"
        return r | {"engine": "local-sandbox"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").strip().lower())


def submit_code(slug: str, language: str, code: str) -> dict:
    prob = get_problem(slug)
    results = []
    compile_error = None
    if JUDGE0_URL:
        for i, t in enumerate(prob["tests"]):
            r = _judge0_run(slug, language, code, t["input"])
            if r["status"] == "Compilation Error":
                compile_error = r["stderr"]
                break
            results.append(_grade(i, t, r))
    else:
        with LocalSession(slug, language, code) as s:
            if s.compile_error:
                compile_error = s.compile_error
            else:
                for i, t in enumerate(prob["tests"]):
                    results.append(_grade(i, t, s.run(t["input"])))
    if compile_error:
        return {"status": "Compilation Error", "stderr": compile_error, "tests": [], "passed": 0, "total": len(prob["tests"]),
                "engine": engine_name()}
    order = ["Compilation Error", "Runtime Error", "Time Limit Exceeded", "Wrong Answer"]
    overall = "Accepted"
    for st in order:
        if any(r["status"] == st for r in results):
            overall = st
            break
    return {"status": overall, "tests": results, "passed": sum(r["status"] == "Passed" for r in results), "total": len(results),
            "time_ms": max([r["time_ms"] for r in results] or [0]), "engine": engine_name(),
            "first_failure": next((r for r in results if r["status"] != "Passed"), None)}


def _grade(i, t, r):
    if r["status"] == "OK":
        st = "Passed" if _norm(r["stdout"]) == _norm(t["expected"]) else "Wrong Answer"
    else:
        st = r["status"]
    return {"index": i, "input": t["input"], "expected": t["expected"], "actual": (r["stdout"] or "").strip(), "stderr": r["stderr"],
            "status": st, "time_ms": r["time_ms"], "tag": t["tag"]}
