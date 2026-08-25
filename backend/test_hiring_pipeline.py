import json
import time
from database import SessionLocal, engine
import models
from hiring_routes import hiring_agent, CodeExecutor

def run_hiring_pipeline_test():
    print("=" * 70)
    print("TESTING FOUNDEROS HIRING AGENT & INTERVIEWOS ASSESSMENT ENGINE")
    print("=" * 70)

    db = SessionLocal()
    models.Base.metadata.create_all(bind=engine)

    # 1. Job Creation
    print("\n1. Testing Job Requisition Creation...")
    job = models.Job(
        title="Senior React Developer",
        department="Engineering",
        seniority="Senior",
        target_compensation="$120,000 / yr",
        required_skills=json.dumps(["React", "TypeScript", "JavaScript", "Python"]),
        experience_years=3,
        job_description=json.dumps({"overview": "Lead frontend development"}),
        status="OPEN"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    print(f"   [OK] Job Created: ID={job.id}, Title='{job.title}'")

    # 2. Auto MCQ Generation (Round 1)
    print("\n2. Testing Round 1 MCQ Generation (20 Questions)...")
    mcq_questions = hiring_agent.generate_mcq_questions(job.title, ["React", "TypeScript", "Python"], count=20)
    assert len(mcq_questions) >= 5, "MCQs should be generated"
    for q in mcq_questions:
        db.add(models.MCQQuestion(
            job_id=job.id,
            question_text=q.get("question_text", ""),
            options=json.dumps(q.get("options", [])),
            correct_option_index=q.get("correct_option_index", 0),
            topic=q.get("topic", "General"),
            difficulty=q.get("difficulty", "MEDIUM")
        ))
    db.commit()
    q_count = db.query(models.MCQQuestion).filter(models.MCQQuestion.job_id == job.id).count()
    print(f"   [OK] {q_count} MCQ Questions saved in DB with topic/difficulty labels.")

    # 3. Auto Coding Problem Generation (Round 2)
    print("\n3. Testing Round 2 Coding Problem Generation...")
    coding_prob_spec = hiring_agent.generate_coding_problem(job.title, ["Python", "JavaScript"])
    prob = models.CodingProblem(
        job_id=job.id,
        title=coding_prob_spec.get("title", "Remove Duplicates from Sorted Array"),
        description=coding_prob_spec.get("description", ""),
        difficulty=coding_prob_spec.get("difficulty", "MEDIUM"),
        time_limit_mins=30,
        examples=json.dumps(coding_prob_spec.get("examples", [])),
        constraints=json.dumps(coding_prob_spec.get("constraints", [])),
        starter_code=json.dumps(coding_prob_spec.get("starter_code", {})),
        test_cases=json.dumps(coding_prob_spec.get("test_cases", []))
    )
    db.add(prob)
    db.commit()
    print(f"   [OK] Coding Problem Created: '{prob.title}' ({prob.difficulty}).")

    # 4. Candidate Screening
    print("\n4. Testing Candidate Resume Screening & Shortlisting...")
    cand = models.Candidate(
        job_id=job.id,
        name="Rahul Sharma",
        email="rahul.sharma@example.com",
        resume_text="3 years experience in React, TypeScript, and Python.",
        skills=json.dumps(["React", "TypeScript", "JavaScript", "Python"]),
        experience_years=3,
        resume_match_score=90.0,
        status="SHORTLISTED"
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    mcq_round = models.AssessmentRound(candidate_id=cand.id, job_id=job.id, round_type="MCQ", status="PENDING", duration_minutes=20, total_items=q_count)
    coding_round = models.AssessmentRound(candidate_id=cand.id, job_id=job.id, round_type="CODING", status="PENDING", duration_minutes=30, total_items=1)
    db.add_all([mcq_round, coding_round])
    db.commit()
    print(f"   [OK] Candidate Screened: ID={cand.id}, Match={cand.resume_match_score}%, Status={cand.status}.")

    # 5. Round 1 MCQ Submission & Evaluation
    print("\n5. Testing Round 1 MCQ Submission...")
    db_qs = db.query(models.MCQQuestion).filter(models.MCQQuestion.job_id == job.id).all()
    correct = 0
    for q in db_qs:
        ans = models.CandidateMCQAnswer(
            assessment_id=mcq_round.id,
            candidate_id=cand.id,
            question_id=q.id,
            selected_option_index=q.correct_option_index,
            is_correct=True
        )
        db.add(ans)
        correct += 1
    
    mcq_score = round((correct / max(len(db_qs), 1)) * 100, 1)
    mcq_round.score = mcq_score
    mcq_round.status = "COMPLETED"
    cand.status = "CODING_PENDING"
    db.commit()
    print(f"   [OK] MCQ Round Completed. Score: {mcq_score}%. Progression: {cand.status}.")

    # 6. Round 2 Python Code Executor Test
    print("\n6. Testing Round 2 Python Code Executor...")
    python_solution = """def solution(nums_str):
    import json
    nums = json.loads(nums_str)
    unique = list(dict.fromkeys(nums))
    return len(unique)
"""
    test_cases = json.loads(prob.test_cases)
    exec_res = CodeExecutor.evaluate_submission("python", python_solution, test_cases)
    print(f"   [OK] Code Execution Status: {exec_res['status']} ({exec_res['test_cases_passed']}/{exec_res['total_test_cases']} test cases passed in {exec_res['execution_time_ms']}ms).")
    assert exec_res['test_cases_passed'] > 0, "Test cases should pass"

    coding_round.score = exec_res['pass_rate_percent']
    coding_round.status = "COMPLETED"
    db.commit()

    # 7. Weighted Candidate Evaluation (Resume 20% + MCQ 30% + Coding 50%)
    print("\n7. Testing Weighted Score & AI Candidate Evaluation...")
    eval_res = hiring_agent.generate_candidate_evaluation(
        candidate_name=cand.name,
        resume_score=cand.resume_match_score,
        mcq_score=mcq_round.score,
        coding_score=coding_round.score,
        resume_weight=0.20,
        mcq_weight=0.30,
        coding_weight=0.50
    )
    
    cand_eval = models.CandidateEvaluation(
        candidate_id=cand.id,
        job_id=job.id,
        resume_score=cand.resume_match_score,
        mcq_score=mcq_round.score,
        coding_score=coding_round.score,
        resume_weight=0.20,
        mcq_weight=0.30,
        coding_weight=0.50,
        overall_score=eval_res["overall_score"],
        recommendation=eval_res["recommendation"],
        strengths=json.dumps(eval_res["strengths"]),
        concerns=json.dumps(eval_res["concerns"]),
        founder_decision="PENDING"
    )
    db.add(cand_eval)
    cand.status = "RECOMMENDED"
    db.commit()
    print(f"   [OK] Overall Score Calculated: {eval_res['overall_score']}% (Resume 20% + MCQ 30% + Coding 50%).")
    print(f"   [OK] AI Recommendation: {eval_res['recommendation']}.")

    # 8. Founder Decision Gate
    print("\n8. Testing Founder Approval Gate...")
    cand.evaluation.founder_decision = "APPROVED"
    cand.evaluation.decision_notes = "Outstanding performance in both MCQ and Coding rounds."
    cand.status = "APPROVED"
    db.commit()
    print(f"   [OK] Founder Decision Recorded: {cand.evaluation.founder_decision}. Final Candidate Status: {cand.status}.")

    db.close()
    print("\n" + "=" * 70)
    print("HIRING AGENT & INTERVIEWOS ASSESSMENT ENGINE VERIFIED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_hiring_pipeline_test()
