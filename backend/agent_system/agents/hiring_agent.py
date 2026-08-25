import time
import json
from typing import Dict, Any, List
from ..gemini_client import GeminiClient

class HiringAgent:
    """
    Hiring Agent: Handles Job Requirements, Resume Screening, 
    Round 1 MCQ Generation, Round 2 Coding Problem Generation, Candidate Scoring, 
    Evaluation & Recommendations for Founder Approval.
    """
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client
        self.name = "HIRING"

    def execute(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        start_time = time.time()
        context = context or {}

        llm_prompt = f"""
You are the expert Talent Acquisition & Technical Hiring AI Agent.
Task Directive: "{prompt}"
Context from Upstream (CEO/Budget): {context}

Generate an exhaustive hiring package. Return ONLY valid JSON with this exact schema:
{{
  "job_title": "Role Title (e.g. Frontend Developer)",
  "department": "Engineering" | "Product" | "Growth" | "Operations",
  "seniority": "Intern" | "Junior" | "Mid-Level" | "Senior" | "Lead",
  "target_compensation": "Estimated salary or stipend (e.g. ₹10k-₹25k/mo or $90k/yr)",
  "experience_years": 2,
  "required_skills": ["React", "JavaScript", "TypeScript", "HTML/CSS"],
  "job_description": {{
    "overview": "Role overview and impact",
    "core_responsibilities": ["Responsibility 1", "Responsibility 2", "Responsibility 3"],
    "must_have_qualifications": ["Qualification 1", "Qualification 2"],
    "growth_and_perks": ["Perk 1", "Perk 2"]
  }},
  "initial_candidates": [
    {{
      "name": "Rahul Sharma",
      "email": "rahul.sharma@example.com",
      "experience_years": 3,
      "skills": ["React", "JavaScript", "TypeScript", "CSS"],
      "resume_match_score": 91.0,
      "status": "SHORTLISTED",
      "resume_text": "3 years experience building responsive web interfaces in React and TypeScript."
    }},
    {{
      "name": "Ananya Patel",
      "email": "ananya.p@example.com",
      "experience_years": 2,
      "skills": ["React", "JavaScript", "Redux", "HTML"],
      "resume_match_score": 88.0,
      "status": "SHORTLISTED",
      "resume_text": "2 years experience in React frontend development and state management."
    }},
    {{
      "name": "Arjun Verma",
      "email": "arjun.v@example.com",
      "experience_years": 1,
      "skills": ["JavaScript", "HTML", "CSS"],
      "resume_match_score": 52.0,
      "status": "REJECTED",
      "resume_text": "Junior developer with basic HTML/JS experience."
    }}
  ]
}}
"""

        fallback = {
            "job_title": "Frontend Developer",
            "department": "Engineering",
            "seniority": "Mid-Level",
            "target_compensation": "₹15,000 - ₹25,000 / month (or $80,000 / yr)",
            "experience_years": 2,
            "required_skills": ["React", "JavaScript", "TypeScript", "HTML/CSS"],
            "job_description": {
                "overview": "Join our founding team to build high-performance web applications and agent dashboards.",
                "core_responsibilities": [
                    "Develop modular components in React, TypeScript, and Tailwind CSS",
                    "Integrate RESTful APIs and real-time WebSocket state updates",
                    "Optimize frontend render performance and accessibility"
                ],
                "must_have_qualifications": [
                    "2+ years experience with React & TypeScript",
                    "Demonstrated portfolio of shipped web applications",
                    "Solid grasp of JavaScript async patterns and DOM rendering"
                ],
                "growth_and_perks": [
                    "Direct founder mentorship",
                    "High equity upside potential",
                    "Flexible remote setup"
                ]
            },
            "initial_candidates": [
                {
                    "name": "Rahul Sharma",
                    "email": "rahul.sharma@example.com",
                    "experience_years": 3,
                    "skills": ["React", "JavaScript", "TypeScript", "CSS"],
                    "resume_match_score": 91.0,
                    "status": "SHORTLISTED",
                    "resume_text": "3 years experience building responsive web interfaces in React and TypeScript."
                },
                {
                    "name": "Ananya Patel",
                    "email": "ananya.p@example.com",
                    "experience_years": 2,
                    "skills": ["React", "JavaScript", "Redux", "HTML"],
                    "resume_match_score": 88.0,
                    "status": "SHORTLISTED",
                    "resume_text": "2 years experience in React frontend development and state management."
                },
                {
                    "name": "Arjun Verma",
                    "email": "arjun.v@example.com",
                    "experience_years": 1,
                    "skills": ["JavaScript", "HTML", "CSS"],
                    "resume_match_score": 52.0,
                    "status": "REJECTED",
                    "resume_text": "Junior developer with basic HTML/JS experience."
                }
            ]
        }

        res = self.gemini.generate_json(
            prompt=llm_prompt,
            system_instruction="You are the Hiring AI Agent. Output strictly valid JSON recruitment deliverables.",
            fallback_data=fallback
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        data = res.get("data", fallback)
        role = data.get("job_title", "Frontend Developer")

        return {
            "agent_name": self.name,
            "intent": "HIRING_PIPELINE_GENERATION",
            "input_prompt": prompt,
            "status": "COMPLETED",
            "result_summary": f"Formulated hiring requirement & resume screening for {role}. Shortlisted top candidate matches.",
            "artifact_payload": data,
            "tokens_used": res.get("tokens_used", 0),
            "execution_time_ms": elapsed_ms
        }

    def generate_mcq_questions(self, role_title: str, required_skills: List[str], count: int = 20) -> List[Dict[str, Any]]:
        """
        Generates role-specific MCQ questions (default 20 questions) with topic, difficulty, options, and correct index.
        """
        skills_str = ", ".join(required_skills) or "React, JavaScript, TypeScript, Web Fundamentals"
        prompt = f"""
Generate exactly {count} technical multiple-choice (MCQ) questions for the role: "{role_title}".
Target Skills: {skills_str}.

Return JSON array of {count} objects:
[
  {{
    "question_text": "What is the primary purpose of React.useMemo hook?",
    "options": [
      "To cache the result of a calculation between re-renders",
      "To mutate DOM directly",
      "To handle side effects on mount",
      "To trigger re-render on state change"
    ],
    "correct_option_index": 0,
    "topic": "React",
    "difficulty": "MEDIUM"
  }}
]
"""

        fallback_questions = [
            {
                "question_text": "Which React hook is designed to memoize expensive calculation values across renders?",
                "options": ["useEffect", "useMemo", "useCallback", "useRef"],
                "correct_option_index": 1,
                "topic": "React",
                "difficulty": "EASY"
            },
            {
                "question_text": "What is the return type of typeof null in JavaScript?",
                "options": ["'null'", "'undefined'", "'object'", "'number'"],
                "correct_option_index": 2,
                "topic": "JavaScript",
                "difficulty": "EASY"
            },
            {
                "question_text": "In TypeScript, what keyword allows creating a type from the keys of an existing type?",
                "options": ["typeof", "keyof", "enum", "extends"],
                "correct_option_index": 1,
                "topic": "TypeScript",
                "difficulty": "MEDIUM"
            },
            {
                "question_text": "Which HTTP status code represents 'Unprocessable Entity'?",
                "options": ["400", "401", "404", "422"],
                "correct_option_index": 3,
                "topic": "Web Fundamentals",
                "difficulty": "MEDIUM"
            },
            {
                "question_text": "How does React fiber architecture achieve non-blocking rendering?",
                "options": [
                    "By running on separate web worker threads",
                    "By breaking render work into units and pausing/prioritizing them",
                    "By compiling JSX directly into WebAssembly",
                    "By disabling virtual DOM comparisons"
                ],
                "correct_option_index": 1,
                "topic": "React",
                "difficulty": "HARD"
            }
        ]

        res = self.gemini.generate_json(
            prompt=prompt,
            system_instruction="Output strictly valid JSON array of MCQ objects.",
            fallback_data={"questions": fallback_questions}
        )
        data = res.get("data", {})
        if isinstance(data, list):
            return data
        return data.get("questions", fallback_questions)

    def generate_coding_problem(self, role_title: str, required_skills: List[str]) -> Dict[str, Any]:
        """
        Generates a role-specific coding problem with problem description, examples, constraints,
        starter code, and test cases.
        """
        skills_str = ", ".join(required_skills) or "React, JavaScript, Python"
        prompt = """
Generate an algorithmic coding problem suitable for a 30-minute Coding Assessment for role: "%s".
Target Skills: %s.

Return JSON object:
{
  "title": "Remove Duplicates from Sorted Array",
  "description": "Given a sorted array `nums`, remove the duplicates in-place such that each element appears only once and return the new length.",
  "difficulty": "MEDIUM",
  "time_limit_mins": 30,
  "examples": [
    {"input": "[1, 1, 2]", "output": "2", "explanation": "Your function should return length = 2, with the first two elements being 1 and 2."}
  ],
  "constraints": [
    "1 <= nums.length <= 3 * 10^4",
    "-100 <= nums[i] <= 100",
    "nums is sorted in non-decreasing order."
  ],
  "starter_code": {
    "python": "def solution(nums_str):\\n    # Write your python code here\\n    # Example input: '[1, 1, 2]'\\n    import json\\n    nums = json.loads(nums_str)\\n    unique = list(dict.fromkeys(nums))\\n    return len(unique)\\n",
    "javascript": "function solution(inputStr) {\\n  const nums = JSON.parse(inputStr);\\n  const unique = Array.from(new Set(nums));\\n  return unique.length;\\n}\\n",
    "java": "public class Solution {\\n    public static void main(String[] args) {\\n        // Java implementation\\n    }\\n}",
    "cpp": "#include <iostream>\\nint main() {\\n    return 0;\\n}"
  },
  "test_cases": [
    {"input": "[1, 1, 2]", "expected_output": "2"},
    {"input": "[0,0,1,1,1,2,2,3,3,4]", "expected_output": "5"},
    {"input": "[1, 2, 3]", "expected_output": "3"}
  ]
}
""" % (role_title, skills_str)

        fallback = {
            "title": "Remove Duplicates from Sorted Array",
            "description": "Given a sorted array `nums`, remove the duplicates in-place such that each element appears only once and return the new length.",
            "difficulty": "MEDIUM",
            "time_limit_mins": 30,
            "examples": [
                {"input": "[1, 1, 2]", "output": "2", "explanation": "Function returns length 2."}
            ],
            "constraints": [
                "1 <= nums.length <= 3 * 10^4",
                "nums is sorted in non-decreasing order."
            ],
            "starter_code": {
                "python": "def solution(nums_str):\n    import json\n    nums = json.loads(nums_str)\n    unique = list(dict.fromkeys(nums))\n    return len(unique)\n",
                "javascript": "function solution(inputStr) {\n  const nums = JSON.parse(inputStr);\n  return Array.from(new Set(nums)).length;\n}\n",
                "java": "// Java starter code",
                "cpp": "// C++ starter code"
            },
            "test_cases": [
                {"input": "[1, 1, 2]", "expected_output": "2"},
                {"input": "[0,0,1,1,1,2,2,3,3,4]", "expected_output": "5"},
                {"input": "[1, 2, 3]", "expected_output": "3"}
            ]
        }

        res = self.gemini.generate_json(
            prompt=prompt,
            system_instruction="Output strictly valid JSON coding problem spec.",
            fallback_data=fallback
        )
        return res.get("data", fallback)

    def generate_candidate_evaluation(
        self, 
        candidate_name: str, 
        resume_score: float, 
        mcq_score: float, 
        coding_score: float,
        resume_weight: float = 0.20,
        mcq_weight: float = 0.30,
        coding_weight: float = 0.50
    ) -> Dict[str, Any]:
        """
        Generates candidate evaluation, weighted score, recommendation, strengths, and concerns.
        """
        overall = round((resume_score * resume_weight) + (mcq_score * mcq_weight) + (coding_score * coding_weight), 1)
        
        if overall >= 85:
            rec = "STRONG_HIRE"
        elif overall >= 75:
            rec = "HIRE"
        elif overall >= 60:
            rec = "RECONSIDER"
        else:
            rec = "REJECT"

        prompt = f"""
Candidate: {candidate_name}
Resume Score (20%): {resume_score}%
MCQ Score (30%): {mcq_score}%
Coding Score (50%): {coding_score}%
Calculated Overall Score: {overall}%
Base Recommendation: {rec}

Generate strengths & concerns analysis. Return JSON:
{{
  "recommendation": "{rec}",
  "strengths": [
    "Strong mastery of core concepts",
    "High execution speed in coding assessment"
  ],
  "concerns": [
    "Minor gaps in edge case handling"
  ]
}}
"""

        fallback = {
            "recommendation": rec,
            "strengths": ["Strong technical foundation", "High score in coding assessment"],
            "concerns": ["Limited experience in large-scale architecture"]
        }

        res = self.gemini.generate_json(
            prompt=prompt,
            system_instruction="Output strictly valid JSON evaluation summary.",
            fallback_data=fallback
        )
        data = res.get("data", fallback)
        data["overall_score"] = overall
        data["recommendation"] = data.get("recommendation", rec)
        return data
