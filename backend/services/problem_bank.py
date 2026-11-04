"""Static problem bank: statements, test cases, execution drivers and per-problem tutor knowledge.

Test cases are run through the real executor; nothing here is an execution result.
"""

# ---------------------------------------------------------------- Java drivers
# Each driver is appended after the user's code in Main.java. It reads stdin, calls Solution and
# prints a canonical output. Fully-qualified names avoid needing imports after the user's classes.
_JAVA_INT_ARRAY = """
    static int[] parseArr(String line) {
        line = line.trim().replace("[", "").replace("]", "");
        if (line.isEmpty()) return new int[0];
        String[] p = line.split(",");
        int[] a = new int[p.length];
        for (int i = 0; i < p.length; i++) a[i] = Integer.parseInt(p[i].trim());
        return a;
    }
"""

JAVA_DRIVERS = {
    "valid-parentheses": """
public class Main {
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        String s = br.readLine();
        if (s == null) s = "";
        s = s.trim();
        if (s.length() >= 2 && s.startsWith("\\"") && s.endsWith("\\"")) s = s.substring(1, s.length() - 1);
        System.out.println(new Solution().isValid(s));
    }
}
""",
    "maximum-subarray": """
public class Main {
%s
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        System.out.println(new Solution().maxSubArray(parseArr(br.readLine())));
    }
}
""" % _JAVA_INT_ARRAY,
    "two-sum": """
public class Main {
%s
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        int[] nums = parseArr(br.readLine());
        int target = Integer.parseInt(br.readLine().trim());
        int[] r = new Solution().twoSum(nums, target);
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < r.length; i++) { if (i > 0) sb.append(","); sb.append(r[i]); }
        System.out.println(sb.append("]"));
    }
}
""" % _JAVA_INT_ARRAY,
    "best-time-to-buy-and-sell-stock": """
public class Main {
%s
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        System.out.println(new Solution().maxProfit(parseArr(br.readLine())));
    }
}
""" % _JAVA_INT_ARRAY,
    "contains-duplicate": """
public class Main {
%s
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        System.out.println(new Solution().containsDuplicate(parseArr(br.readLine())));
    }
}
""" % _JAVA_INT_ARRAY,
    "climbing-stairs": """
public class Main {
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        System.out.println(new Solution().climbStairs(Integer.parseInt(br.readLine().trim())));
    }
}
""",
    "house-robber": """
public class Main {
%s
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        System.out.println(new Solution().rob(parseArr(br.readLine())));
    }
}
""" % _JAVA_INT_ARRAY,
}

_PY_PARSE = """
import sys, json
def _arr(l):
    l = l.strip()
    return json.loads(l if l.startswith('[') else '[' + l + ']')
_lines = sys.stdin.read().split('\\n')
"""
PYTHON_DRIVERS = {
    "valid-parentheses": _PY_PARSE + "_s=_lines[0].strip().strip('\"')\nprint(str(Solution().isValid(_s)).lower())\n",
    "maximum-subarray": _PY_PARSE + "print(Solution().maxSubArray(_arr(_lines[0])))\n",
    "two-sum": _PY_PARSE + "print('['+','.join(map(str,Solution().twoSum(_arr(_lines[0]), int(_lines[1]))))+']')\n",
    "best-time-to-buy-and-sell-stock": _PY_PARSE + "print(Solution().maxProfit(_arr(_lines[0])))\n",
    "contains-duplicate": _PY_PARSE + "print(str(Solution().containsDuplicate(_arr(_lines[0]))).lower())\n",
    "climbing-stairs": _PY_PARSE + "print(Solution().climbStairs(int(_lines[0])))\n",
    "house-robber": _PY_PARSE + "print(Solution().rob(_arr(_lines[0])))\n",
}

# ---------------------------------------------------------------- Problems
PROBLEMS = {
    "valid-parentheses": {
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "topics": ["Stacks"],
        "pattern": "Stack matching (LIFO)",
        "statement": "Given a string containing '(', ')', '{', '}', '[' and ']', determine whether the input string is valid. "
                     "A string is valid if every opening bracket is closed by the same type of bracket, in the correct order.",
        "constraints": ["1 ≤ s.length ≤ 10^4", "s consists only of the characters ()[]{}"],
        "examples": [
            {"input": '"()"', "output": "true"},
            {"input": '"()[]{}"', "output": "true"},
            {"input": '"(]"', "output": "false"},
            {"input": '"([)]"', "output": "false"},
            {"input": '"{[]}"', "output": "true"},
        ],
        "complexity": {"time": "O(n)", "space": "O(n)"},
        "related": ["Min Stack", "Generate Parentheses", "Longest Valid Parentheses"],
        "tests": [
            {"input": "()", "expected": "true", "tag": "basic"},
            {"input": "()[]{}", "expected": "true", "tag": "basic"},
            {"input": "(]", "expected": "false", "tag": "logic"},
            {"input": "([)]", "expected": "false", "tag": "logic"},
            {"input": "{[]}", "expected": "true", "tag": "basic"},
            {"input": "]", "expected": "false", "tag": "edge"},
            {"input": "((", "expected": "false", "tag": "edge"},
        ],
        "starter": {
            "java": "class Solution {\n    public boolean isValid(String s) {\n        // your code here\n        return false;\n    }\n}\n",
            "python": "class Solution:\n    def isValid(self, s: str) -> bool:\n        pass\n",
        },
        "company_weight": {"Zscaler": 5, "Microsoft": 3},
        "oa_frequency": 9, "interview_frequency": 7, "learning_order": 1,
        "next_problem": "maximum-subarray",
    },
    "maximum-subarray": {
        "title": "Maximum Subarray",
        "difficulty": "Medium",
        "topics": ["Arrays", "Dynamic Programming"],
        "pattern": "Kadane's algorithm (running best)",
        "statement": "Given an integer array nums, find the contiguous subarray (containing at least one number) with the largest sum and return its sum.",
        "constraints": ["1 ≤ nums.length ≤ 10^5", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "[-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "note": "Optimal subarray: [4,-1,2,1]"}],
        "complexity": {"time": "O(n)", "space": "O(1)"},
        "related": ["Maximum Product Subarray", "Best Time to Buy and Sell Stock", "Maximum Sum Circular Subarray"],
        "tests": [
            {"input": "-2,1,-3,4,-1,2,1,-5,4", "expected": "6", "tag": "basic"},
            {"input": "1", "expected": "1", "tag": "edge"},
            {"input": "5,4,-1,7,8", "expected": "23", "tag": "basic"},
            {"input": "-3,-1,-2", "expected": "-1", "tag": "edge"},
            {"input": "-1", "expected": "-1", "tag": "edge"},
        ],
        "starter": {
            "java": "class Solution {\n    public int maxSubArray(int[] nums) {\n        // your code here\n        return 0;\n    }\n}\n",
            "python": "class Solution:\n    def maxSubArray(self, nums):\n        pass\n",
        },
        "company_weight": {"Zscaler": 4, "Microsoft": 3},
        "oa_frequency": 8, "interview_frequency": 7, "learning_order": 3,
        "next_problem": "best-time-to-buy-and-sell-stock",
    },
    "two-sum": {
        "title": "Two Sum",
        "difficulty": "Easy",
        "topics": ["Hashing", "Arrays"],
        "pattern": "Complement lookup with a HashMap",
        "statement": "Given an integer array nums and an integer target, return the indices of the two numbers whose sum equals target. "
                     "Each input has exactly one solution and you may not use the same element twice.",
        "constraints": ["2 ≤ nums.length ≤ 10^4", "-10^9 ≤ nums[i], target ≤ 10^9", "Exactly one valid answer exists"],
        "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"}],
        "complexity": {"time": "O(n)", "space": "O(n)"},
        "related": ["Contains Duplicate", "3Sum", "Two Sum II (sorted input)"],
        "tests": [
            {"input": "2,7,11,15\n9", "expected": "[0,1]", "tag": "basic"},
            {"input": "3,2,4\n6", "expected": "[1,2]", "tag": "logic"},
            {"input": "3,3\n6", "expected": "[0,1]", "tag": "edge"},
            {"input": "-1,-2,-3,-4,-5\n-8", "expected": "[2,4]", "tag": "edge"},
            {"input": "0,4,3,0\n0", "expected": "[0,3]", "tag": "edge"},
        ],
        "starter": {
            "java": "import java.util.HashMap;\n\nclass Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // your code here\n        return new int[]{-1, -1};\n    }\n}\n",
            "python": "class Solution:\n    def twoSum(self, nums, target):\n        pass\n",
        },
        "company_weight": {"Microsoft": 4, "Zscaler": 2},
        "oa_frequency": 6, "interview_frequency": 8, "learning_order": 1,
        "next_problem": "best-time-to-buy-and-sell-stock",
    },
    "best-time-to-buy-and-sell-stock": {
        "title": "Best Time to Buy and Sell Stock",
        "difficulty": "Easy",
        "topics": ["Arrays"],
        "pattern": "Running minimum (one pass)",
        "statement": "Given an array prices where prices[i] is the price of a stock on day i, return the maximum profit achievable by buying on one day "
                     "and selling on a later day. If no profit is possible, return 0.",
        "constraints": ["1 ≤ prices.length ≤ 10^5", "0 ≤ prices[i] ≤ 10^4"],
        "examples": [{"input": "[7,1,5,3,6,4]", "output": "5", "note": "Buy at 1 (day 1), sell at 6 (day 4)"}],
        "complexity": {"time": "O(n)", "space": "O(1)"},
        "related": ["Maximum Subarray", "Best Time to Buy and Sell Stock II", "Trapping Rain Water"],
        "tests": [
            {"input": "7,1,5,3,6,4", "expected": "5", "tag": "basic"},
            {"input": "7,6,4,3,1", "expected": "0", "tag": "edge"},
            {"input": "5", "expected": "0", "tag": "edge"},
            {"input": "2,4,1", "expected": "2", "tag": "logic"},
            {"input": "3,3,3", "expected": "0", "tag": "edge"},
        ],
        "starter": {
            "java": "class Solution {\n    public int maxProfit(int[] prices) {\n        // your code here\n        return 0;\n    }\n}\n",
            "python": "class Solution:\n    def maxProfit(self, prices):\n        pass\n",
        },
        "company_weight": {"Microsoft": 5, "Zscaler": 3},
        "oa_frequency": 7, "interview_frequency": 9, "learning_order": 2,
        "next_problem": "maximum-subarray",
    },
    "contains-duplicate": {
        "title": "Contains Duplicate",
        "difficulty": "Easy",
        "topics": ["Hashing", "Arrays"],
        "pattern": "Seen-set membership",
        "statement": "Given an integer array nums, return true if any value appears at least twice, and false if every element is distinct.",
        "constraints": ["1 ≤ nums.length ≤ 10^5"],
        "examples": [{"input": "[1,2,3,1]", "output": "true"}, {"input": "[1,2,3,4]", "output": "false"}],
        "complexity": {"time": "O(n)", "space": "O(n)"},
        "related": ["Two Sum", "Contains Duplicate II"],
        "tests": [
            {"input": "1,2,3,1", "expected": "true", "tag": "basic"},
            {"input": "1,2,3,4", "expected": "false", "tag": "basic"},
            {"input": "1", "expected": "false", "tag": "edge"},
        ],
        "starter": {
            "java": "import java.util.HashSet;\n\nclass Solution {\n    public boolean containsDuplicate(int[] nums) {\n        return false;\n    }\n}\n",
            "python": "class Solution:\n    def containsDuplicate(self, nums):\n        pass\n",
        },
        "company_weight": {"Microsoft": 2},
        "oa_frequency": 5, "interview_frequency": 5, "learning_order": 2,
        "next_problem": "two-sum",
    },
}

PROBLEMS["climbing-stairs"] = {
    "title": "Climbing Stairs", "difficulty": "Easy", "topics": ["Dynamic Programming"], "pattern": "1-D DP (Fibonacci recurrence)",
    "statement": "You are climbing a staircase with n steps. Each time you can climb 1 or 2 steps. In how many distinct ways can you reach the top?",
    "constraints": ["1 ≤ n ≤ 45"], "examples": [{"input": "n = 3", "output": "3", "note": "1+1+1, 1+2, 2+1"}],
    "complexity": {"time": "O(n)", "space": "O(1)"}, "related": ["House Robber", "Min Cost Climbing Stairs", "Fibonacci Number"],
    "tests": [{"input": "1", "expected": "1", "tag": "edge"}, {"input": "2", "expected": "2", "tag": "basic"}, {"input": "3", "expected": "3", "tag": "basic"},
              {"input": "5", "expected": "8", "tag": "logic"}, {"input": "45", "expected": "1836311903", "tag": "edge"}],
    "starter": {"java": "class Solution {\n    public int climbStairs(int n) {\n        return 0;\n    }\n}\n", "python": "class Solution:\n    def climbStairs(self, n):\n        pass\n"},
    "company_weight": {"Microsoft": 3}, "oa_frequency": 6, "interview_frequency": 6, "learning_order": 1, "next_problem": "house-robber",
}
PROBLEMS["house-robber"] = {
    "title": "House Robber", "difficulty": "Medium", "topics": ["Dynamic Programming"], "pattern": "1-D DP (take / skip)",
    "statement": "Houses along a street hold nums[i] money. Adjacent houses have connected alarms, so you cannot rob two adjacent houses. Return the maximum amount you can rob.",
    "constraints": ["1 ≤ nums.length ≤ 100", "0 ≤ nums[i] ≤ 400"], "examples": [{"input": "[2,7,9,3,1]", "output": "12", "note": "Rob houses 0, 2, 4: 2 + 9 + 1"}],
    "complexity": {"time": "O(n)", "space": "O(1)"}, "related": ["House Robber II", "Climbing Stairs", "Delete and Earn"],
    "tests": [{"input": "1,2,3,1", "expected": "4", "tag": "basic"}, {"input": "2,7,9,3,1", "expected": "12", "tag": "basic"}, {"input": "5", "expected": "5", "tag": "edge"},
              {"input": "2,1,1,2", "expected": "4", "tag": "logic"}, {"input": "0,0,0", "expected": "0", "tag": "edge"}],
    "starter": {"java": "class Solution {\n    public int rob(int[] nums) {\n        return 0;\n    }\n}\n", "python": "class Solution:\n    def rob(self, nums):\n        pass\n"},
    "company_weight": {"Microsoft": 4, "Zscaler": 2}, "oa_frequency": 7, "interview_frequency": 8, "learning_order": 2, "next_problem": "maximum-subarray",
}

# Exact demo code from the brief (used only as editor presets — never as results).
DEMO_SNIPPETS = {
    "valid-parentheses": {
        "Counter approach (buggy)": """class Solution {
    public boolean isValid(String s) {
        int open = 0;

        for (char ch : s.toCharArray()) {
            if (ch == '(' || ch == '[' || ch == '{') {
                open++;
            } else {
                open--;
            }

            if (open < 0) return false;
        }

        return open == 0;
    }
}
""",
        "Stack solution": """import java.util.Stack;

class Solution {
    public boolean isValid(String s) {
        Stack<Character> stack = new Stack<>();

        for (char ch : s.toCharArray()) {

            if (ch == '(' || ch == '[' || ch == '{') {
                stack.push(ch);
            } else {
                if (stack.isEmpty()) return false;

                char top = stack.pop();

                if ((ch == ')' && top != '(') ||
                    (ch == ']' && top != '[') ||
                    (ch == '}' && top != '{')) {
                    return false;
                }
            }
        }

        return stack.isEmpty();
    }
}
""",
    },
    "maximum-subarray": {
        "Kadane's algorithm": """class Solution {
    public int maxSubArray(int[] nums) {
        int best = nums[0];
        int current = nums[0];

        for (int i = 1; i < nums.length; i++) {
            current = Math.max(nums[i], current + nums[i]);
            best = Math.max(best, current);
        }

        return best;
    }
}
""",
    },
    "two-sum": {
        "HashMap solution": """import java.util.HashMap;

class Solution {
    public int[] twoSum(int[] nums, int target) {
        HashMap<Integer, Integer> map = new HashMap<>();

        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];

            if (map.containsKey(complement)) {
                return new int[]{map.get(complement), i};
            }

            map.put(nums[i], i);
        }

        return new int[]{-1, -1};
    }
}
""",
    },
    "best-time-to-buy-and-sell-stock": {
        "Running minimum": """class Solution {
    public int maxProfit(int[] prices) {
        int minPrice = Integer.MAX_VALUE;
        int bestProfit = 0;

        for (int price : prices) {
            minPrice = Math.min(minPrice, price);
            bestProfit = Math.max(bestProfit, price - minPrice);
        }

        return bestProfit;
    }
}
""",
    },
}


DEMO_SNIPPETS["climbing-stairs"] = {"Bottom-up DP": """class Solution {
    public int climbStairs(int n) {
        if (n <= 2) return n;
        int prev2 = 1, prev1 = 2;
        for (int i = 3; i <= n; i++) {
            int cur = prev1 + prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
"""}
DEMO_SNIPPETS["house-robber"] = {
    "Greedy every-other (buggy)": """class Solution {
    public int rob(int[] nums) {
        int even = 0, odd = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i % 2 == 0) even += nums[i];
            else odd += nums[i];
        }
        return Math.max(even, odd);
    }
}
""",
    "DP take/skip": """class Solution {
    public int rob(int[] nums) {
        int prev2 = 0, prev1 = 0;
        for (int x : nums) {
            int cur = Math.max(prev1, prev2 + x);
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
""",
}


def get_problem(slug: str) -> dict:
    p = PROBLEMS.get(slug)
    if not p:
        raise KeyError(slug)
    return {"slug": slug, **p}


def public_problem(slug: str) -> dict:
    p = get_problem(slug)
    return {k: v for k, v in p.items() if k not in ("company_weight",)} | {
        "snippets": DEMO_SNIPPETS.get(slug, {}),
        "tests": [{"input": t["input"], "expected": t["expected"], "tag": t["tag"]} for t in p["tests"]],
    }
