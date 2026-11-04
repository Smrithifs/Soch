"""Rule-based tutor: intent classification + code analysis + problem knowledge. No LLM."""
import re

from .knowledge import KB
from .problem_bank import PROBLEMS

# ------------------------------------------------------------------ intent classification
INTENT_RULES = [  # (intent, regex) — checked in order, first match wins
    ("failed_approach", r"why.*(fail|wrong|not work|incorrect)|what('?s| is) wrong|failing|wrong answer|my logic"),
    ("bug", r"\bbug\b|find (the )?(bug|error|issue)|debug|fix (my|the) code|error in"),
    ("explain_code", r"line by line|explain (my|this|the) code|walk.*through.*code|what does (my|this) code"),
    ("why_ds", r"why.*(stack|hash ?map|map|hash ?set|set\b|data structure|track|lowest|min)|need a (stack|map)"),
    ("complexity", r"complexit|big ?o|\btime\b|\bspace\b|how fast|memory|o\(n"),
    ("edge_cases", r"edge|corner|test cases?|what inputs|break my"),
    ("hint", r"\bhint|nudge|stuck|clue|without (revealing|giving)"),
    ("pattern", r"pattern|technique|which approach|what kind of problem|category"),
    ("optimal", r"optimal|best solution|show.*solution|correct solution|full solution|how to solve"),
    ("alternatives", r"alternative|another way|other way|different approach|without"),
    ("similar", r"similar|next problem|related|practice next|what next|recommend"),
    ("brute", r"brute|naive|simplest"),
    ("one_liner", r"one sentence|summar|interview answer|elevator"),
    ("explain_problem", r"explain (the )?problem|what (is|does) (the|this) problem|understand|what are we|restate|meaning"),
]


def classify(question: str, slug: str) -> str:
    q = question.lower().strip()
    for rx, intent in KB[slug].get("specific", []):
        if re.search(rx, q):
            return intent
    for intent, rx in INTENT_RULES:
        if re.search(rx, q):
            return intent
    return "unknown"


# ------------------------------------------------------------------ code analysis
def _strip_comments(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return re.sub(r"(//|#).*", "", code)


def loop_depth(code: str, language: str) -> int:
    code = _strip_comments(code)
    if language == "python":
        depth, stack = 0, []
        for line in code.splitlines():
            if not line.strip():
                continue
            ind = len(line) - len(line.lstrip())
            while stack and stack[-1] >= ind:
                stack.pop()
            if re.match(r"\s*(for|while)\b", line):
                stack.append(ind)
                depth = max(depth, len(stack))
        return depth
    depth, best, braces = 0, 0, []
    tokens = re.finditer(r"\b(for|while)\b|\{|\}", code)
    pending = 0
    for t in tokens:
        s = t.group(0)
        if s in ("for", "while"):
            pending += 1
        elif s == "{":
            braces.append(pending > 0)
            if pending:
                depth += 1
                pending -= 1
                best = max(best, depth)
        else:
            if braces and braces.pop():
                depth -= 1
    return max(best, 1 if re.search(r"\b(for|while)\b", code) else 0)


def analyze_code(code: str, language: str = "java") -> dict:
    c = _strip_comments(code or "")
    f = {
        "stack": bool(re.search(r"\bStack\s*<|Deque|ArrayDeque|\.push\(|\bstack\b\s*=\s*\[\]", c)),
        "hashmap": bool(re.search(r"HashMap|Map\s*<|\{\}\s*$|dict\(|=\s*\{\s*\}", c, re.M)),
        "hashset": bool(re.search(r"HashSet|Set\s*<|set\(\)", c)),
        "sort": bool(re.search(r"Arrays\.sort|\.sort\(|sorted\(", c)),
        "recursion": False,
        "loops": loop_depth(c, language),
        "counter_only": False,
        "array_alloc": bool(re.search(r"new\s+(int|char|boolean|long)\s*\[\s*[a-zA-Z]", c)),
    }
    f["counter_only"] = not f["stack"] and bool(re.search(r"\+\+|--|\+=\s*1|-=\s*1", c)) and not f["hashmap"]
    # derived complexity
    if f["loops"] >= 3:
        time = "O(n³)"
    elif f["loops"] == 2:
        time = "O(n²)"
    elif f["sort"]:
        time = "O(n log n)"
    elif f["loops"] == 1:
        time = "O(n)"
    else:
        time = "O(1)"
    space = "O(n)" if (f["stack"] or f["hashmap"] or f["hashset"] or f["array_alloc"]) else "O(1)"
    why_t = {"O(n³)": "three nested loops over the input", "O(n²)": "two nested loops over the input", "O(n log n)": "sorting dominates",
             "O(n)": "a single pass over the input with O(1) work per element", "O(1)": "no loop over the input"}[time]
    ds = "a stack" if f["stack"] else "a HashMap" if f["hashmap"] else "a HashSet" if f["hashset"] else "an extra array" if f["array_alloc"] else None
    why_s = f"{ds} that can grow to n elements" if ds else "only a fixed number of scalar variables"
    f.update(time=time, space=space, why_time=why_t, why_space=why_s)
    return f


def detect_bugs(slug: str, code: str, last: dict | None) -> list[str]:
    c = _strip_comments(code or "")
    a = analyze_code(code)
    bugs = []
    if slug == "valid-parentheses":
        if a["counter_only"]:
            bugs.append("**Logic error — counting can't validate type or order.** Your code tracks *how many* brackets are open, not *which* ones. "
                        "For `\"(]\"`: `(` makes `open = 1`, `]` makes `open = 0`, the loop ends and `open == 0` returns **true** — but `]` never matched `(`. "
                        "`\"([)]\"` passes the same way. You need to remember the *type* of each open bracket in order → a stack.")
        if a["stack"] and re.search(r"\.pop\(\)", c) and not re.search(r"isEmpty\(\)|size\(\)\s*==\s*0|not\s+stack|len\(stack\)", c):
            bugs.append("**Runtime risk:** you call `pop()` without checking `isEmpty()` first. Input `\"]\"` throws `EmptyStackException`.")
        if a["stack"] and re.search(r"return\s+true\s*;\s*\}\s*\}\s*$", c.strip()):
            bugs.append("**Edge case:** returning `true` at the end ignores unclosed openers like `\"((\"`. Return `stack.isEmpty()`.")
    if slug == "maximum-subarray":
        if re.search(r"(best|max\w*|ans|res\w*)\s*=\s*0\s*;", c):
            bugs.append("**Edge case error:** initialising the best sum to `0` returns 0 for all-negative arrays like `[-3,-1,-2]` (expected -1). Start from `nums[0]`.")
        if a["loops"] >= 2:
            bugs.append(f"**Complexity:** {a['loops']} nested loops → {a['time']}. With n = 10^5 this will exceed the time limit; Kadane is O(n).")
    if slug == "two-sum":
        put = re.search(r"\.put\(", c)
        chk = re.search(r"containsKey|\.get\(", c)
        if put and chk and put.start() < chk.start():
            bugs.append("**Logic error:** you insert `nums[i]` *before* checking its complement, so an element can pair with itself — `[3,2,4]`, target 6 returns `[0,0]`. Check first, then put.")
        if a["loops"] >= 2:
            bugs.append("**Complexity:** nested loops make this O(n²). It's correct but slower than the O(n) HashMap approach interviewers expect.")
    if slug == "house-robber":
        if re.search(r"%\s*2", c):
            bugs.append("**Logic error — greedy every-other house.** Summing all even or all odd indices misses cases where skipping *two* houses is best: "
                        "`[2,1,1,2]` gives max(3, 3) = 3, but robbing houses 0 and 3 gives **4**. You need DP: at each house choose max(skip, take + best two back).")
    if slug == "best-time-to-buy-and-sell-stock":
        if re.search(r"min\w*\s*=\s*0\s*;", c, re.I):
            bugs.append("**Logic error:** `minPrice` starts at 0, so `price - minPrice` is just the price. Start at `Integer.MAX_VALUE` (or `prices[0]`).")
        if re.search(r"Integer\.MIN_VALUE", c) and re.search(r"(best|profit|max)\w*\s*=\s*Integer\.MIN_VALUE", c, re.I):
            bugs.append("**Edge case error:** starting profit at `Integer.MIN_VALUE` returns a negative number for decreasing prices. Profit should start at 0 (don't trade).")
        if a["loops"] >= 2:
            bugs.append("**Complexity:** nested loops → O(n²); track the running minimum to get O(n).")
    if last and last.get("status") == "Compilation Error":
        bugs.insert(0, f"**Syntax error — it doesn't compile:**\n```\n{(last.get('stderr') or '')[:600]}\n```")
    if last and last.get("status") == "Runtime Error":
        ff = last.get("first_failure") or {}
        bugs.insert(0, f"**Runtime error** on input `{ff.get('input', '')}`:\n```\n{(ff.get('stderr') or last.get('stderr') or '')[:500]}\n```")
    return bugs


# ------------------------------------------------------------------ line-by-line explanation
LINE_RULES = [
    (r"^import\s+java\.util\.Stack", "Imports Java's `Stack` class."),
    (r"^import\s+java\.util\.HashMap", "Imports `HashMap` for O(1) average lookups."),
    (r"^import", "Imports a library class."),
    (r"^class\s+Solution|^public\s+class", "Declares the `Solution` class the judge calls."),
    (r"public\s+boolean\s+isValid", "Method signature: takes the bracket string, returns whether it's valid."),
    (r"public\s+int\s+maxSubArray", "Method signature: returns the largest contiguous subarray sum."),
    (r"public\s+int\[\]\s+twoSum", "Method signature: returns the two indices as an int array."),
    (r"public\s+int\s+maxProfit", "Method signature: returns the best single-trade profit."),
    (r"Stack<Character>\s+\w+\s*=", "Creates an empty stack that will hold every opening bracket that hasn't been matched yet."),
    (r"HashMap<Integer,\s*Integer>\s+\w+\s*=", "Creates the map: **value → index** of numbers seen so far."),
    (r"int\s+open\s*=\s*0", "A single counter of currently open brackets — note it can't tell `(` from `[`."),
    (r"for\s*\(\s*char\s+\w+\s*:\s*\w+\.toCharArray", "Loops over each character once — this is the O(n) pass."),
    (r"for\s*\(\s*int\s+price\s*:", "Visits each day's price once, left to right."),
    (r"for\s*\(\s*int\s+i\s*=\s*1", "Starts at index 1 because index 0 already seeded the variables."),
    (r"for\s*\(\s*int\s+i\s*=\s*0", "Loops over each index once."),
    (r"if\s*\(\s*ch\s*==\s*'\('\s*\|\|", "Checks whether the character is an opening bracket."),
    (r"\.push\(", "Pushes the opener; it is now the most recent unmatched bracket (top of the stack)."),
    (r"open\+\+", "Counts one more open bracket (type is forgotten)."),
    (r"open--", "Treats *any* closing bracket as closing *any* opener — this is where `(]` slips through."),
    (r"if\s*\(\s*open\s*<\s*0\s*\)", "Catches a closer with nothing open, e.g. `)(`."),
    (r"return\s+open\s*==\s*0", "Returns true when counts balance — but balanced counts ≠ valid ordering/types."),
    (r"if\s*\(\s*\w+\.isEmpty\(\)\s*\)\s*return\s+false", "A closer with nothing open is invalid — and this guard prevents `pop()` on an empty stack."),
    (r"char\s+top\s*=\s*\w+\.pop\(\)", "Removes the most recent opener to compare with the current closer (LIFO)."),
    (r"\(\s*ch\s*==\s*'\)'\s*&&\s*top\s*!=\s*'\('", "Type check: each closer must match the opener that was popped."),
    (r"return\s+\w+\.isEmpty\(\)", "Valid only if no openers are left unmatched."),
    (r"int\s+best\s*=\s*nums\[0\]", "Best sum seen so far — seeded with the first element so all-negative arrays work."),
    (r"int\s+current\s*=\s*nums\[0\]", "Best sum of a subarray **ending at the current index**."),
    (r"current\s*=\s*Math\.max\(\s*nums\[i\]", "Extend the previous subarray or restart at `nums[i]` — whichever is larger."),
    (r"best\s*=\s*Math\.max\(\s*best", "Remember the largest `current` ever seen."),
    (r"int\s+complement\s*=", "The value that would complete the pair with `nums[i]`."),
    (r"if\s*\(\s*\w+\.containsKey\(\s*complement", "O(1) check: did we already see the complement?"),
    (r"return\s+new\s+int\[\]\s*\{\s*\w+\.get\(", "Found it — return the earlier index and the current index."),
    (r"\.put\(\s*nums\[i\]\s*,\s*i\s*\)", "Record this value and its index *after* the check, so an element never pairs with itself."),
    (r"return\s+new\s+int\[\]\s*\{\s*-1", "Fallback if no pair exists (the problem guarantees one does)."),
    (r"int\s+minPrice\s*=\s*Integer\.MAX_VALUE", "Lowest price so far; MAX_VALUE so the first price always replaces it."),
    (r"int\s+bestProfit\s*=\s*0", "Best profit so far; 0 means 'don't trade' when prices only fall."),
    (r"minPrice\s*=\s*Math\.min", "Update the cheapest buy day seen up to today."),
    (r"bestProfit\s*=\s*Math\.max", "Profit if we sold today; keep it if it's the best so far."),
    (r"return\s+(best|bestProfit)\s*;", "Return the answer."),
    (r"return\s+false\s*;", "Mismatch → the string is invalid."),
    (r"^\}+$", None),
]


def explain_lines(code: str) -> str:
    out = []
    for n, raw in enumerate((code or "").splitlines(), 1):
        line = raw.strip()
        if not line or line in ("}", "{", "})", "};"):
            continue
        msg = next((m for rx, m in LINE_RULES if re.search(rx, line)), None)
        if msg is None:
            if re.match(r"^\}?\s*else", line):
                msg = "Otherwise branch — handles the closing-bracket case." if "{" in line else "Otherwise branch."
            elif line.startswith("if"):
                msg = "Condition check."
            elif line.startswith("||") or line.startswith("("):
                msg = "Continues the type-matching condition."
            elif line.startswith("return"):
                msg = "Returns a result."
            else:
                msg = "Statement."
        out.append(f"- `L{n}` `{line[:70]}` — {msg}")
    return "\n".join(out) if out else "Paste or write some code in the editor first, then ask again."


# ------------------------------------------------------------------ main entry
def respond(slug: str, question: str, code: str, language: str, last_result: dict | None, hint_level: int, profile_level: str = "Beginner",
            mode: str | None = None) -> dict:
    if slug not in KB:
        return {"intent": "unknown", "title": "Unknown problem", "body": "Open a problem first."}
    k, pr = KB[slug], PROBLEMS[slug]
    intent = mode or classify(question or "", slug)
    a = analyze_code(code, language)
    ctx = [f"problem: {pr['title']}", f"code: {a['time']} time / {a['space']} space (static analysis)"]
    if last_result:
        ctx.append(f"last run: {last_result.get('status')} ({last_result.get('passed', '?')}/{last_result.get('total', '?')})")
    title, body, extra = "", "", {}

    if intent in k.get("answers", {}):
        title, body = "Answer", k["answers"][intent]
    elif intent == "explain_problem":
        title = "Problem explained"
        ex = pr["examples"][0]
        body = f"{k['explain']}\n\n**Example:** `{ex['input']}` → `{ex['output']}`" + (f" — {ex['note']}" if ex.get("note") else "") + \
               f"\n\nTarget: **{pr['complexity']['time']} time, {pr['complexity']['space']} space**."
    elif intent == "hint":
        lvl = min(hint_level, len(k["hints"]) - 1)
        title = f"Hint {lvl + 1} of {len(k['hints'])}"
        body = k["hints"][lvl] + ("\n\n_Ask again for a stronger hint._" if lvl < len(k["hints"]) - 1 else "\n\n_That's the last hint — try coding it now._")
        extra["hint_level_used"] = lvl + 1
    elif intent == "pattern":
        title, body = "Pattern", k["pattern"] + f"\n\nYou'll see the same pattern in: {', '.join(k['similar'][:2])}."
    elif intent == "why_ds":
        title, body = "Why this data structure", k["why_ds"]
        if slug == "valid-parentheses" and a["counter_only"]:
            body += "\n\nYour current code uses a counter — that's exactly why `\"(]\"` returns true."
    elif intent == "explain_code":
        title, body = "Your code, line by line", explain_lines(code)
    elif intent == "complexity":
        title = "Complexity of your current code"
        body = (f"- **Time: {a['time']}** — {a['why_time']}.\n- **Space: {a['space']}** — {a['why_space']}.\n\n"
                f"Optimal for this problem: {pr['complexity']['time']} time, {pr['complexity']['space']} space.")
        if a["time"] != pr["complexity"]["time"]:
            body += f"\n\n⚠️ Your time complexity is worse than optimal — see the bottleneck: {k['brute']}"
        if last_result and last_result.get("status") not in (None, "Accepted"):
            body += f"\n\nNote: your last submission was **{last_result['status']}** — complexity only matters once it's correct."
    elif intent == "edge_cases":
        title = "Edge cases to test"
        body = "\n".join(f"- {e}" for e in k["edge_cases"])
        if last_result and last_result.get("first_failure"):
            ff = last_result["first_failure"]
            body = f"Your last submission already fails on `{ff['input']}` (expected `{ff['expected']}`, got `{ff['actual'] or ff['status']}`).\n\n" + body
    elif intent in ("failed_approach", "bug"):
        bugs = detect_bugs(slug, code, last_result)
        ff = (last_result or {}).get("first_failure")
        title = "Why it fails" if intent == "failed_approach" else "Bug report"
        if not last_result:
            body = "I haven't seen an execution of this code yet. Press **Submit** so I can read the real test results.\n\n"
        elif last_result.get("status") == "Accepted":
            body = f"Your last submission was **Accepted** ({last_result.get('passed')}/{last_result.get('total')} tests). Nothing is failing.\n\n"
        elif ff:
            body = (f"**{last_result['status']}** on test #{ff['index'] + 1}: input `{ff['input']}` — expected `{ff['expected']}`, "
                    f"your code printed `{ff['actual'] or '(nothing)'}`.\n\n")
        body += "\n\n".join(bugs) if bugs else ("I couldn't match a known bug pattern. Trace the failing input by hand line by line and compare each variable with what you expect."
                                                  if last_result and last_result.get("status") != "Accepted" else "No known bug patterns detected in the current code.")
    elif intent == "optimal":
        title, body = "Optimal approach", k["optimal"] + f"\n\n{k['why_ds']}"
    elif intent == "alternatives":
        title, body = "Alternative approaches", k["alternatives"]
    elif intent == "similar":
        title, body = "Similar problems", "\n".join(f"- {s}" for s in k["similar"])
    elif intent == "brute":
        title, body = "Brute force", k["brute"]
    elif intent == "one_liner":
        title, body = "Interview one-liner", f"> {k['one_liner']}"
    else:
        title = "Can you clarify?"
        body = (f"I can help with **{pr['title']}**. Try asking: why your code fails, a hint, the pattern, why we use the data structure, "
                f"complexity of your code, edge cases, a line-by-line explanation, alternatives or similar problems.")
    return {"intent": intent, "title": title, "body": body, "context": ctx, **extra}
