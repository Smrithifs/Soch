"""Problem-specific tutor knowledge, revision-card bank, ThinkMap content and interview rubrics.
Pure data — the decision logic lives in the *_engine modules."""

KB = {
    "valid-parentheses": {
        "explain": "You get a string of brackets. It is valid only if every closing bracket matches the **type** of the most recent "
                   "unmatched opening bracket, and nothing is left open at the end. So `([])` is valid, but `(]` (wrong type) and "
                   "`([)]` (wrong order) are not.",
        "hints": [
            "Look at `([)]`. When you see `)`, which opening bracket must it close? Is it the first one you saw, or the latest one?",
            "You need to remember opening brackets in the order you saw them and always check the **most recent** one first. Which data structure gives you 'last in, first out'?",
            "Push each opening bracket. On a closing bracket: if nothing is open → invalid; otherwise pop and compare the types. At the end, what must be true about what's left?",
        ],
        "pattern": "**Stack matching (LIFO).** Whenever the most recently opened thing must be closed first — brackets, HTML tags, undo — the pattern is a stack.",
        "why_ds": "**Why a stack?** A closing bracket must match the *most recently opened* bracket that is still unmatched. A stack is LIFO "
                  "(last in, first out): `push` on every opener, and on a closer `pop` gives exactly that most-recent opener to compare against. "
                  "A counter only knows *how many* brackets are open, not *which type* or *in what order*.",
        "brute": "Repeatedly delete adjacent pairs `()`, `[]`, `{}` until nothing changes; valid if the string becomes empty. That is O(n²) because each pass is O(n) and you may need n/2 passes.",
        "optimal": "One pass with a stack: push openers; on a closer, fail if the stack is empty or the popped opener has a different type; at the end return `stack.isEmpty()`. O(n) time, O(n) space.",
        "edge_cases": ["`\"]\"` — closer with nothing open (must not call pop on an empty stack)", "`\"((\"` — openers left at the end",
                       "`\"(]\"` — correct count, wrong type", "`\"([)]\"` — correct types, wrong order", "Odd length strings are always invalid (quick early exit)",
                       "Very long input (10^4) — make sure you stay O(n)"],
        "alternatives": "**Without a stack?** For a *single* bracket type, a counter works (`open++`/`open--`, never below zero). With three types you must remember the "
                        "order of types, which is exactly what a stack stores. You can *simulate* a stack with a `char[]` and a top index (same O(n) space, a bit faster than `java.util.Stack`), "
                        "or use the O(n²) pair-removal method, but there is no correct O(1)-space approach for mixed types.",
        "similar": ["Min Stack — stack that also tracks a running property", "Daily Temperatures — monotonic stack", "Longest Valid Parentheses — stack of indices"],
        "specific": [
            (r"without\s+(a\s+|using\s+(a\s+)?)?stack|no\s+stack", "alternatives"),
            (r"\(\]|counting|counter|open\+\+", "failed_approach"),
        ],
        "one_liner": "I scan once, pushing every opening bracket on a stack; each closing bracket must pop a matching opener, and the string is valid only if the stack ends empty — O(n) time and space.",
    },
    "maximum-subarray": {
        "explain": "Among all contiguous slices of the array, find the one whose elements add up to the most and return that sum. The slice must contain at least one element, "
                   "so for an all-negative array the answer is the largest (least negative) single element.",
        "hints": [
            "Suppose you know the best subarray sum that **ends at index i-1**. What are the only two choices for the best subarray ending at index i?",
            "Either you extend the previous subarray (`previous + nums[i]`) or you start fresh at `nums[i]`. When is starting fresh better?",
            "Keep two variables: `current` (best sum ending here) and `best` (best seen anywhere). Initialise both with `nums[0]`, not 0.",
        ],
        "pattern": "**Kadane's algorithm / 1-D dynamic programming.** State = best sum ending at i; transition = extend or restart.",
        "why_ds": "No extra data structure is needed — just two running integers. That's why space is O(1).",
        "brute": "Try every (start, end) pair and sum it: O(n³), or O(n²) with a running sum. With n up to 10^5 that is ~10^10 operations, far too slow.",
        "optimal": "Kadane: `current = max(nums[i], current + nums[i])`, `best = max(best, current)`. One pass, O(n) time, O(1) space.",
        "edge_cases": ["All negative `[-3,-1,-2]` → `-1` (initialising best to 0 gives the wrong answer 0)", "Single element `[5]` or `[-1]`",
                       "Large positive run then big negative dip `[5,4,-1,7,8]`", "Max length 10^5 — must be linear"],
        "alternatives": "Divide and conquer (best of left half, right half, or crossing the middle) runs in O(n log n). Prefix sums: answer = max over j of `prefix[j] - min(prefix[i<j])` — O(n), same idea as the stock problem.",
        "similar": ["Best Time to Buy and Sell Stock — same running-min/prefix idea", "Maximum Product Subarray — track min and max", "Maximum Sum Circular Subarray"],
        "specific": [
            (r"current\s*=|math\.max\s*\(\s*nums|extend|restart|start fresh", "kadane_line"),
            (r"all[\s-]*negative|negative", "all_negative"),
            (r"all subarrays|checking all|better than|brute", "brute"),
        ],
        "answers": {
            "kadane_line": "`current = Math.max(nums[i], current + nums[i])` decides, at each index, whether the best subarray **ending at i** should "
                           "*extend* the previous one (`current + nums[i]`) or *restart* at `nums[i]`. If the running sum `current` has become negative, "
                           "adding it only hurts, so `nums[i]` alone is larger and we restart. `best` then remembers the largest `current` ever seen.",
            "all_negative": "Because both `best` and `current` start at `nums[0]` (not 0), and `current = max(nums[i], current + nums[i])` always includes at least one element, "
                            "an all-negative array like `[-3,-1,-2]` returns `-1`, the largest single element. If you initialised `best = 0`, you'd wrongly return 0 — an empty subarray.",
            "brute": "Checking all subarrays is O(n²) even with a running sum (O(n³) naively). Kadane reuses the answer for index i-1 to get index i in O(1), so the whole scan is O(n). For n = 10^5 that's 10^5 steps instead of ~5×10^9.",
        },
        "one_liner": "I keep the best sum of a subarray ending at the current index — extend it or restart, whichever is larger — and track the maximum, giving O(n) time and O(1) space.",
    },
    "two-sum": {
        "explain": "Find two **different positions** i and j such that `nums[i] + nums[j] == target`, and return `[i, j]`. Exactly one answer exists. You return indices, not the values.",
        "hints": [
            "For each number x, what other value would you need to reach the target? Give that value a name.",
            "That needed value is `target - x` (the complement). The slow part is *searching* for it. What structure answers 'have I seen this value, and where?' in O(1)?",
            "Walk once. For each index, first check whether the complement was seen before; only then record the current value and its index. Why does that order matter?",
        ],
        "pattern": "**Complement lookup with a hash map** (one-pass hashing). Store what you've seen; ask whether the partner you need is already stored.",
        "why_ds": "**Why a HashMap?** For each `nums[i]` you need to know instantly whether its complement `target - nums[i]` appeared earlier **and at which index**. "
                  "A `HashMap<Integer, Integer>` maps *value → index* of previously seen numbers, with average O(1) `containsKey`/`get`. "
                  "A `HashSet` would tell you *whether* it exists, but not *where*; an array scan would cost O(n) per lookup.",
        "brute": "Nested loops: for each i, check every j > i. That is n(n-1)/2 pairs → O(n²) time, O(1) space.",
        "optimal": "One pass: compute `complement = target - nums[i]`; if the map contains it, return `[map.get(complement), i]`; else `map.put(nums[i], i)`. O(n) time, O(n) space.",
        "edge_cases": ["Duplicates `[3,3]`, target 6 → `[0,1]`", "Same element can't be used twice: `[3,2,4]`, target 6 must not return `[0,0]`",
                       "Negative numbers `[-1,-2,-3,-4,-5]`, target -8", "Zeros `[0,4,3,0]`, target 0", "Answer at the very end of the array"],
        "alternatives": "Sort a copy of (value, index) pairs and use two pointers from both ends: O(n log n) time, O(n) space for the pairs. Useful when the input is already sorted (Two Sum II) — then O(1) extra space.",
        "similar": ["Best Time to Buy and Sell Stock — next on your path: one pass with remembered state", "Contains Duplicate — seen-set", "3Sum — two-sum inside a loop"],
        "specific": [
            (r"complement", "complement"),
            (r"duplicate|\[\s*3\s*,\s*3\s*\]|same number", "duplicates"),
            (r"nested|better than|brute|two loops", "brute_vs"),
        ],
        "answers": {
            "complement": "The **complement** is the value that would complete the pair: `complement = target - nums[i]`. With `nums = [2,7,11,15]`, `target = 9`: at i=0 the complement is 7 — "
                          "not in the map yet, so store `2 → 0`. At i=1 the complement is `9 - 7 = 2`, which *is* in the map at index 0, so return `[0, 1]`.",
            "duplicates": "With `[3,3]`, target 6: at i=0 the complement 3 is not in the map yet (it's empty), so you store `3 → 0`. At i=1 the complement 3 **is** in the map at index 0 → return `[0,1]`. "
                          "It works because you check *before* inserting — the current element can only match an *earlier* one. If you inserted first, `[3,2,4]` with target 6 would wrongly return `[0,0]`.",
            "brute_vs": "Nested loops compare every pair: ~n²/2 checks, O(n²). The HashMap turns the inner search into an O(1) lookup, so total work is O(n). "
                        "For n = 10^4: ~5×10^7 comparisons vs 10^4 lookups. The trade-off is O(n) extra memory for the map.",
        },
        "one_liner": "I make one pass, and for each number look up its complement in a hash map of earlier values to indices — O(n) time, O(n) space.",
    },
    "best-time-to-buy-and-sell-stock": {
        "explain": "Pick one day to buy and a **later** day to sell to maximise `sell - buy`. If prices only fall, you don't trade and the profit is 0.",
        "hints": [
            "If you were to sell today, which past day would you have wanted to buy on?",
            "The best buy day for selling today is simply the cheapest day so far. Can you keep that in one variable as you scan?",
            "Track `minPrice` so far and `bestProfit`; for each price update the minimum, then compare `price - minPrice` with the best.",
        ],
        "pattern": "**Running minimum / one-pass state tracking** (a special case of Kadane on price differences).",
        "why_ds": "**Why track the lowest price?** For any sell day, the best profit comes from buying at the minimum price seen *before* it. Keeping `minPrice` while scanning left-to-right "
                  "guarantees the buy day is always earlier than the sell day, and gives that optimum in O(1) per day.",
        "brute": "Try every buy day i and every later sell day j: O(n²). With 10^5 days that's ~5×10^9 pairs.",
        "optimal": "`minPrice = min(minPrice, price)`; `bestProfit = max(bestProfit, price - minPrice)` for each price. O(n) time, O(1) space.",
        "edge_cases": ["Strictly decreasing `[7,6,4,3,1]` → 0", "Single day `[5]` → 0", "All equal `[3,3,3]` → 0",
                       "Minimum appears after the maximum `[2,4,1]` → 2 (don't just do max - min)", "Large input 10^5 — linear only"],
        "alternatives": "Convert to daily differences and run Kadane's maximum subarray (clamped at 0). Same O(n)/O(1), useful to show you see the connection.",
        "similar": ["Maximum Subarray — same idea on differences", "Best Time to Buy and Sell Stock II — multiple transactions (greedy)", "Trapping Rain Water — running max from both sides"],
        "specific": [
            (r"only decreas|decreasing|keeps? falling|prices? (drop|fall)", "decreasing"),
            (r"lowest|track.*(min|low)|min(imum)?\s*price|why.*min", "why_ds"),
            (r"one sentence|interview|summari[sz]e|elevator", "one_liner"),
        ],
        "answers": {
            "decreasing": "If prices only decrease, e.g. `[7,6,4,3,1]`, every day becomes the new `minPrice`, so `price - minPrice` is always 0 and `bestProfit` stays at its initial 0. "
                          "That's the correct answer: you simply don't trade. This is why `bestProfit` must start at 0, not `Integer.MIN_VALUE`.",
        },
        "one_liner": "I scan once, keeping the lowest price seen so far and the best profit from selling at today's price, which gives O(n) time and O(1) space.",
    },
    "contains-duplicate": {
        "explain": "Return true if any value appears at least twice.",
        "hints": ["What do you need to remember about numbers you've already seen?", "A HashSet answers 'seen before?' in O(1).", "Add each number; if add() returns false, it's a duplicate."],
        "pattern": "**Seen-set membership.**", "why_ds": "A HashSet gives O(1) average membership checks.",
        "brute": "Compare all pairs: O(n²).", "optimal": "HashSet, one pass: O(n) time, O(n) space. Or sort first: O(n log n), O(1).",
        "edge_cases": ["Single element", "All same", "Negative values"], "alternatives": "Sort and compare neighbours.",
        "similar": ["Two Sum", "Contains Duplicate II"], "specific": [], "one_liner": "I add each number to a hash set and return true the first time an insert finds it already present.",
    },
}

KB["climbing-stairs"] = {
    "explain": "Count the distinct sequences of 1-steps and 2-steps that add up to n.",
    "hints": ["How can you arrive at step n? What was the very last move?", "The last move was 1 step (from n-1) or 2 steps (from n-2). So ways(n) = ?",
              "ways(n) = ways(n-1) + ways(n-2), with ways(1)=1, ways(2)=2. Keep only the last two values."],
    "pattern": "**1-D DP (Fibonacci recurrence).** Answer for n is built from answers for n-1 and n-2.",
    "why_ds": "Only the previous two answers are needed, so two integers replace the whole dp array → O(1) space.",
    "brute": "Plain recursion ways(n-1)+ways(n-2) recomputes the same subproblems — O(2^n).",
    "optimal": "Iterate i = 3..n keeping prev1, prev2: cur = prev1 + prev2. O(n) time, O(1) space.",
    "edge_cases": ["n = 1 → 1", "n = 2 → 2", "n = 45 → 1836311903 (fits in int; n = 46 would overflow)"],
    "alternatives": "Memoized recursion (top-down) is O(n)/O(n). Matrix exponentiation gives O(log n).",
    "similar": ["House Robber — same 'look back two' DP", "Min Cost Climbing Stairs", "Decode Ways"], "specific": [],
    "one_liner": "The number of ways to reach step n is the sum of the ways to reach n-1 and n-2, which I compute bottom-up with two variables.",
}
KB["house-robber"] = {
    "explain": "Pick a set of non-adjacent houses with the largest total. Taking house i forbids i-1 and i+1.",
    "hints": ["Stand at house i. What are your only two choices?", "Skip it → best is whatever you had up to i-1. Take it → nums[i] plus the best up to i-2.",
              "best(i) = max(best(i-1), best(i-2) + nums[i]). Keep two rolling variables."],
    "pattern": "**1-D DP — take or skip.** State: best total using houses 0..i. Transition: max(skip, take).",
    "why_ds": "No data structure — dp[i] only depends on dp[i-1] and dp[i-2], so two variables suffice.",
    "brute": "Try every subset of non-adjacent houses: exponential, O(2^n).",
    "optimal": "cur = max(prev1, prev2 + x); prev2 = prev1; prev1 = cur. O(n) time, O(1) space.",
    "edge_cases": ["Single house [5] → 5", "[2,1,1,2] → 4 (skipping two in a row is allowed — even/odd greedy fails)", "All zeros", "Two houses → max of them"],
    "alternatives": "Top-down memoized recursion rob(i) = max(rob(i+1), nums[i] + rob(i+2)). Same O(n).",
    "similar": ["House Robber II — circular street", "Delete and Earn — reduces to House Robber", "Climbing Stairs"],
    "specific": [(r"even|odd|alternate|every other", "greedy")],
    "answers": {"greedy": "Taking every other house (all even or all odd indices) fails on `[2,1,1,2]`: even = 3, odd = 3, but the best is 2 + 2 = **4** — skipping *two* houses in a row is sometimes optimal. DP considers skip vs take at every house, so it finds that."},
    "one_liner": "At each house I either skip it and keep the best so far, or take it plus the best from two houses back, keeping two rolling values for O(n) time and O(1) space.",
}

# ------------------------------------------------------------------ Revision card bank
CARDS = {
    "arrays_index": {"topic": "Arrays", "concept": "Array indexing cost", "q": "What is the time complexity of reading `nums[i]` from an array?",
                     "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"], "correct": 0,
                     "explain": "Arrays are contiguous, so the address of index i is computed directly: base + i × size → O(1)."},
    "arrays_scan": {"topic": "Arrays", "concept": "Single-pass scans", "q": "Finding the maximum of an unsorted array of n numbers needs at least…",
                    "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "correct": 2,
                    "explain": "Every element could be the maximum, so each must be looked at once → O(n)."},
    "hashmap_lookup": {"topic": "Hashing", "concept": "HashMap lookup cost", "q": "Average time complexity of `map.containsKey(x)` on a Java HashMap?",
                       "options": ["O(n)", "O(1)", "O(log n)", "O(n²)"], "correct": 1,
                       "explain": "The key's hash picks a bucket directly; with a good hash and load factor that's O(1) on average (O(n) worst case)."},
    "hashmap_store": {"topic": "Hashing", "concept": "What the Two Sum map stores", "q": "In the one-pass Two Sum solution, the HashMap stores…",
                      "options": ["index → value", "value → index of earlier elements", "complement → count", "sum → pair"], "correct": 1,
                      "explain": "We look up a complement *value* and need its *index*, so the map is value → index for elements seen so far."},
    "complexity_nested": {"topic": "Time Complexity", "concept": "Nested loop cost", "q": "Two nested loops, each running over all n elements, cost…",
                          "options": ["O(n)", "O(2n)", "O(n log n)", "O(n²)"], "correct": 3,
                          "explain": "For each of n outer iterations the inner loop runs n times → n × n = O(n²)."},
    "complexity_single": {"topic": "Time Complexity", "concept": "Time-space trade-off", "q": "One pass using a HashMap of up to n entries costs…",
                          "options": ["O(n) time, O(1) space", "O(n) time, O(n) space", "O(n²) time, O(n) space", "O(log n) time, O(n) space"], "correct": 1,
                          "explain": "One pass = O(n) time; the map may hold n entries = O(n) space."},
    "stack_lifo": {"topic": "Stacks", "concept": "LIFO order", "q": "You push A, B, C onto a stack. What does the next `pop()` return?",
                   "options": ["A", "B", "C", "It throws"], "correct": 2,
                   "explain": "Stacks are Last-In-First-Out: the most recently pushed element (C) comes out first."},
    "stack_parens": {"topic": "Stacks", "concept": "Why counters fail for brackets", "q": "Why does an open/close counter return the wrong answer for `\"(]\"`?",
                     "options": ["It overflows", "It ignores bracket type and order", "It needs sorting", "It's O(n²)"], "correct": 1,
                     "explain": "The count goes 1 → 0 and looks balanced, but `]` doesn't match `(`. Only a stack remembers which type was opened last."},
    "kadane_reset": {"topic": "Arrays", "concept": "Kadane restart rule", "q": "In Kadane's algorithm, when do we restart the running sum at `nums[i]`?",
                     "options": ["When nums[i] is negative", "When the running sum before i is negative", "Every k steps", "Never"], "correct": 1,
                     "explain": "If `current` is negative, `current + nums[i] < nums[i]`, so starting fresh at nums[i] is better."},
    "stock_min": {"topic": "Arrays", "concept": "Running minimum", "q": "In Best Time to Buy and Sell Stock, what single value must you carry while scanning?",
                  "options": ["Maximum price so far", "Minimum price so far", "Sum of prices", "Number of days"], "correct": 1,
                  "explain": "The best buy for selling today is the cheapest earlier price, so track the running minimum."},
    "dp_state": {"topic": "Dynamic Programming", "concept": "Defining the DP state", "q": "For House Robber, what should dp[i] mean?",
                 "options": ["Money in house i", "Best total using houses 0..i", "Number of houses robbed", "Whether house i is robbed"], "correct": 1,
                 "explain": "A good state answers the question for a prefix: dp[i] = best total from houses 0..i. Then the answer is dp[n-1]."},
    "dp_recurrence": {"topic": "Dynamic Programming", "concept": "Writing the recurrence", "q": "Ways to climb n stairs taking 1 or 2 steps: ways(n) = ?",
                      "options": ["ways(n-1) × 2", "ways(n-1) + ways(n-2)", "n + ways(n-1)", "ways(n-2) + 1"], "correct": 1,
                      "explain": "The last move is either 1 step (from n-1) or 2 steps (from n-2); add both counts."},
    "dp_base": {"topic": "Dynamic Programming", "concept": "Base cases & overlapping subproblems", "q": "Why is plain recursion for Climbing Stairs slow?",
                "options": ["Recursion is always slow in Java", "It recomputes the same subproblems exponentially many times", "It needs sorting", "Stack overflow at n=3"], "correct": 1,
                "explain": "ways(n-2) is computed by both ways(n) and ways(n-1), and so on down — O(2^n). Storing results (DP) makes it O(n)."},
    # ---- "what is the output?" code cards
    "out_hashmap": {"topic": "Hashing", "concept": "Output: HashMap overwrite", "type": "code",
                    "q": "What does this print?", "code": "Map<Integer,Integer> m = new HashMap<>();\nm.put(3, 0);\nm.put(3, 1);\nSystem.out.println(m.get(3) + \" \" + m.size());",
                    "options": ["0 1", "1 1", "1 2", "0 2"], "correct": 1,
                    "explain": "put() with an existing key overwrites the value, so get(3) = 1 and the map still has one key. This is why Two Sum stores the latest index for duplicates."},
    "out_stack": {"topic": "Stacks", "concept": "Output: stack order", "type": "code",
                  "q": "What does this print?", "code": "Stack<Character> st = new Stack<>();\nfor (char c : \"([{\".toCharArray()) st.push(c);\nSystem.out.println(st.pop() + \"\" + st.peek());",
                  "options": ["([", "{[", "[{", "{("], "correct": 1,
                  "explain": "pop() removes the last pushed '{'; peek() then shows '[' without removing it → \"{[\"."},
    "out_kadane": {"topic": "Arrays", "concept": "Output: trace Kadane", "type": "code",
                   "q": "What does this print for nums = {-2, 3, -1, 2}?", "code": "int best = nums[0], cur = nums[0];\nfor (int i = 1; i < nums.length; i++) {\n    cur = Math.max(nums[i], cur + nums[i]);\n    best = Math.max(best, cur);\n}\nSystem.out.println(best);",
                   "options": ["3", "4", "2", "5"], "correct": 1,
                   "explain": "cur: -2 → 3 (restart) → 2 → 4. best ends at 4 (subarray [3,-1,2])."},
    "out_loop": {"topic": "Time Complexity", "concept": "Output: count loop work", "type": "code",
                 "q": "How many times does count++ run for n = 4?", "code": "int count = 0;\nfor (int i = 0; i < n; i++)\n    for (int j = i + 1; j < n; j++)\n        count++;",
                 "options": ["16", "8", "6", "4"], "correct": 2,
                 "explain": "Pairs i<j: 3+2+1+0 = 6 = n(n-1)/2. That's why 'check all pairs' is O(n²)."},
    "out_dp": {"topic": "Dynamic Programming", "concept": "Output: trace House Robber", "type": "code",
               "q": "What does this return for nums = {2, 1, 1, 2}?", "code": "int prev2 = 0, prev1 = 0;\nfor (int x : nums) {\n    int cur = Math.max(prev1, prev2 + x);\n    prev2 = prev1; prev1 = cur;\n}\nreturn prev1;",
               "options": ["3", "4", "2", "6"], "correct": 1,
               "explain": "prev1 goes 2 → 2 → 3 → 4. Taking houses 0 and 3 (2+2) beats every-other (3)."},
    "out_minprice": {"topic": "Arrays", "concept": "Output: running minimum", "type": "code",
                     "q": "What does maxProfit return for prices = {3, 8, 1, 4}?", "code": "int minP = Integer.MAX_VALUE, best = 0;\nfor (int p : prices) {\n    minP = Math.min(minP, p);\n    best = Math.max(best, p - minP);\n}\nreturn best;",
                     "options": ["3", "5", "7", "4"], "correct": 1,
                     "explain": "Buy at 3, sell at 8 → 5. Later min becomes 1 but 4-1 = 3 < 5."},
}

# Topic → revision cards (ordered by priority within the topic)
TOPIC_CARDS = {
    "Arrays": ["arrays_index", "out_kadane", "arrays_scan", "stock_min", "out_minprice", "kadane_reset"],
    "Hashing": ["hashmap_lookup", "out_hashmap", "hashmap_store"],
    "Stacks": ["stack_lifo", "out_stack", "stack_parens"],
    "Stacks and Queues": ["stack_lifo", "out_stack", "stack_parens"],
    "Time Complexity": ["complexity_nested", "out_loop", "complexity_single"],
    "Dynamic Programming": ["dp_state", "out_dp", "dp_recurrence", "dp_base", "kadane_reset"],
}

# ------------------------------------------------------------------ Six-month roadmap
ROADMAP = [
    ("Arrays", [], 2), ("Strings", ["Arrays"], 2), ("Hashing", ["Arrays"], 2), ("Two Pointers", ["Arrays"], 2),
    ("Sliding Window", ["Two Pointers", "Hashing"], 2), ("Linked Lists", ["Arrays"], 2), ("Stacks and Queues", ["Arrays"], 2),
    ("Binary Search", ["Arrays"], 2), ("Recursion", ["Arrays"], 2), ("Trees and BST", ["Recursion", "Stacks and Queues"], 2),
    ("Heaps", ["Trees and BST"], 1), ("Graphs", ["Trees and BST", "Stacks and Queues"], 2), ("Greedy", ["Arrays", "Heaps"], 1),
    ("Dynamic Programming", ["Recursion", "Arrays"], 2),
]
TOPIC_ALIASES = {"Stacks": "Stacks and Queues", "Stack": "Stacks and Queues", "Queues": "Stacks and Queues", "Trees": "Trees and BST", "DP": "Dynamic Programming"}

# ------------------------------------------------------------------ ThinkMap
THINKMAP_STEPS = ["Understand the problem", "Input and output", "Constraints", "Brute force", "Bottleneck",
                  "Data structure selection", "Optimized approach", "Complexity", "Edge cases", "Validation"]


def thinkmap_content(slug: str, prob: dict) -> list[dict]:
    k = KB[slug]
    ex = prob["examples"][0]
    io = f"Input: {ex['input']} → Output: {ex['output']}" + (f" ({ex['note']})" if ex.get("note") else "")
    bottleneck = {
        "valid-parentheses": "Counting brackets loses type and order information; repeated pair removal rescans the string.",
        "maximum-subarray": "Re-summing overlapping subarrays — the sum ending at i is recomputed from scratch for each start.",
        "two-sum": "The inner loop *searches* for the partner value — an O(n) search done n times.",
        "best-time-to-buy-and-sell-stock": "For each sell day you rescan all earlier days to find the cheapest buy.",
        "contains-duplicate": "Comparing every pair to find a repeat.",
        "climbing-stairs": "Naive recursion recomputes ways(k) for the same k again and again — exponential.",
        "house-robber": "Trying every subset of houses; greedy every-other misses cases like [2,1,1,2].",
    }[slug]
    validation = f"Dry-run `{prob['tests'][0]['input'].splitlines()[0]}` by hand, then Submit to run all {len(prob['tests'])} tests."
    bodies = [k["explain"], io, " · ".join(prob["constraints"]), k["brute"], bottleneck, k["why_ds"], k["optimal"],
              f"Target: {prob['complexity']['time']} time, {prob['complexity']['space']} space.", " · ".join(k["edge_cases"][:4]), validation]
    return [{"id": f"n{i+1}", "title": t, "body": b} for i, (t, b) in enumerate(zip(THINKMAP_STEPS, bodies))]


# ------------------------------------------------------------------ Interview rubrics
# Each step: (dimension, question, keyword groups). A group is satisfied if any synonym appears.
def interview_steps(slug: str, prob: dict) -> list[dict]:
    t, s = prob["complexity"]["time"].lower(), prob["complexity"]["space"].lower()
    R = {
        "best-time-to-buy-and-sell-stock": {
            "understanding": [["buy", "purchase"], ["sell"], ["later", "after", "before", "future"], ["profit", "difference", "max"]],
            "approach": [["min", "lowest", "cheapest"], ["profit", "difference"], ["one pass", "single pass", "scan", "iterate", "loop"]],
            "brute": [["every pair", "all pairs", "nested", "two loops", "each pair", "each day"], ["n^2", "n²", "n2", "quadratic"]],
            "optimization": [["min", "lowest", "cheapest"], ["so far", "running", "track", "remember", "keep"]],
            "ds": [["variable", "no extra", "constant", "two variables", "no data structure", "integers"]],
            "edge": [["decreas", "falling", "drop"], ["single", "one day", "one element", "empty"], ["equal", "same", "zero profit", "return 0"]],
        },
        "two-sum": {
            "understanding": [["indices", "index", "positions"], ["target", "sum"], ["same element", "twice", "different"]],
            "approach": [["complement", "target -", "difference"], ["map", "hash"]],
            "brute": [["nested", "every pair", "two loops", "all pairs"], ["n^2", "n²", "n2", "quadratic"]],
            "optimization": [["hash", "map"], ["o(1)", "constant", "lookup"]],
            "ds": [["hashmap", "hash map", "dictionary", "map"], ["index", "value"]],
            "edge": [["duplicate", "3,3", "same value"], ["negative"], ["zero"]],
        },
        "valid-parentheses": {
            "understanding": [["type", "kind", "match"], ["order", "nested", "recent"]],
            "approach": [["stack"], ["push"], ["pop", "top", "peek"]],
            "brute": [["remove", "replace", "delete"], ["pair", "()", "adjacent"], ["n^2", "n²", "quadratic"]],
            "optimization": [["stack"], ["one pass", "single pass", "once"]],
            "ds": [["stack", "deque"], ["lifo", "last in", "most recent"]],
            "edge": [["empty"], ["left", "remaining", "unclosed", "leftover"], ["closing first", "starts with", "]"]],
        },
        "maximum-subarray": {
            "understanding": [["contiguous", "subarray", "consecutive"], ["largest", "maximum", "max"], ["sum"]],
            "approach": [["kadane", "running", "current"], ["extend", "restart", "reset", "start fresh"]],
            "brute": [["every", "all subarrays", "nested", "pairs"], ["n^2", "n²", "n^3", "n³", "quadratic", "cubic"]],
            "optimization": [["ending at", "ends at", "current"], ["max", "best"]],
            "ds": [["variable", "constant", "no extra", "two variables"]],
            "edge": [["negative"], ["single", "one element"]],
        },
    }[slug if slug in ("best-time-to-buy-and-sell-stock", "two-sum", "valid-parentheses", "maximum-subarray") else "two-sum"]
    tg = [[t, t.replace("o(", "").replace(")", ""), "linear" if t == "o(n)" else t]]
    sg = [[s, "constant" if s == "o(1)" else "linear", "o(1)" if s == "o(1)" else "o(n)"]]
    return [
        {"dimension": "Problem understanding", "q": f"Here's the problem: **{prob['title']}**. {prob['statement']} Before solving, restate the problem in your own words — what exactly are we returning?", "groups": R["understanding"]},
        {"dimension": "Approach", "q": "Talk me through your overall approach at a high level. What's the key idea?", "groups": R["approach"]},
        {"dimension": "Brute force", "q": "What would a brute-force solution look like, and what does it cost?", "groups": R["brute"]},
        {"dimension": "Optimization", "q": "Where is the brute force wasting work, and how do you remove that waste?", "groups": R["optimization"]},
        {"dimension": "Data structure selection", "q": "Which data structures (if any) do you need, and why that choice?", "groups": R["ds"]},
        {"dimension": "Time complexity", "q": "What is the time complexity of your optimized solution? Justify it.", "groups": tg},
        {"dimension": "Space complexity", "q": "And the space complexity?", "groups": sg},
        {"dimension": "Edge cases", "q": "Which edge cases would you test before saying you're done?", "groups": R["edge"]},
        {"dimension": "Code correctness", "q": f"Write the solution in the Practice Arena and Submit it (I'll read your latest real submission for {prob['title']}). Type 'done' when submitted, or describe your code.", "groups": []},
        {"dimension": "Communication", "q": "Finally — summarise your solution in one or two sentences, as you would to close the interview.", "groups": [["because", "so", "since", "which"], ["o("], ["pass", "scan", "iterate", "loop", "lookup"]]},
    ]
