import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
from agent_system.gemini_client import GeminiClient
from agent_system.agents.hiring_agent import HiringAgent
from code_executor import CodeExecutor

router = APIRouter(prefix="/api/hiring", tags=["Hiring Agent & Assessment Engine"])

gemini_client = GeminiClient()
hiring_agent = HiringAgent(gemini_client)

# -----------------------------------------------------------------
# 1. Job Requisition Endpoints
# -----------------------------------------------------------------
@router.post("/jobs")
def create_hiring_job(
    req: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: Optional[Any] = Depends(auth.get_current_user_optional if hasattr(auth, "get_current_user_optional") else lambda: None)
):
    user_id = current_user.id if current_user else None

    # Use Hiring Agent to generate full job spec & initial candidates
    exec_res = hiring_agent.execute(f"Create hiring job requirement for {req.title}")
    artifact = exec_res.get("artifact_payload", {})

    job = models.Job(
        user_id=user_id,
        title=req.title or artifact.get("job_title", "Frontend Developer"),
        department=req.department or artifact.get("department", "Engineering"),
        seniority=req.seniority or artifact.get("seniority", "Mid-Level"),
        target_compensation=req.target_compensation or artifact.get("target_compensation", "$90,000 / yr"),
        required_skills=json.dumps(req.required_skills or artifact.get("required_skills", ["React", "JavaScript", "TypeScript"])),
        experience_years=req.experience_years or artifact.get("experience_years", 2),
        job_description=json.dumps(artifact.get("job_description", {})),
        status="OPEN"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Auto-generate 20 MCQ questions for Round 1
    mcq_list = hiring_agent.generate_mcq_questions(job.title, req.required_skills or ["React", "JavaScript", "TypeScript"], count=20)
    for q in mcq_list:
        mcq_rec = models.MCQQuestion(
            job_id=job.id,
            question_text=q.get("question_text", ""),
            options=json.dumps(q.get("options", [])),
            correct_option_index=q.get("correct_option_index", 0),
            topic=q.get("topic", "General"),
            difficulty=q.get("difficulty", "MEDIUM")
        )
        db.add(mcq_rec)

    # Auto-generate Coding Problem for Round 2
    coding_prob = hiring_agent.generate_coding_problem(job.title, req.required_skills or ["React", "JavaScript", "Python"])
    coding_rec = models.CodingProblem(
        job_id=job.id,
        title=coding_prob.get("title", "Remove Duplicates from Sorted Array"),
        description=coding_prob.get("description", ""),
        difficulty=coding_prob.get("difficulty", "MEDIUM"),
        time_limit_mins=coding_prob.get("time_limit_mins", 30),
        examples=json.dumps(coding_prob.get("examples", [])),
        constraints=json.dumps(coding_prob.get("constraints", [])),
        starter_code=json.dumps(coding_prob.get("starter_code", {})),
        test_cases=json.dumps(coding_prob.get("test_cases", []))
    )
    db.add(coding_rec)
    db.commit()

    # Seed initial candidates from screening if available
    initial_cands = artifact.get("initial_candidates", [])
    for cand_data in initial_cands:
        cand = models.Candidate(
            job_id=job.id,
            user_id=user_id,
            name=cand_data.get("name", "Candidate"),
            email=cand_data.get("email", "candidate@example.com"),
            resume_text=cand_data.get("resume_text", ""),
            skills=json.dumps(cand_data.get("skills", [])),
            experience_years=cand_data.get("experience_years", 2),
            resume_match_score=cand_data.get("resume_match_score", 85.0),
            status=cand_data.get("status", "SHORTLISTED")
        )
        db.add(cand)
        db.commit()
        db.refresh(cand)

        # Create MCQ Assessment Round
        mcq_round = models.AssessmentRound(
            candidate_id=cand.id,
            job_id=job.id,
            round_type="MCQ",
            status="PENDING" if cand.status == "SHORTLISTED" else "FAILED",
            duration_minutes=20,
            total_items=len(mcq_list)
        )
        db.add(mcq_round)
        
        # Create Coding Assessment Round
        coding_round = models.AssessmentRound(
            candidate_id=cand.id,
            job_id=job.id,
            round_type="CODING",
            status="PENDING",
            duration_minutes=30,
            total_items=1
        )
        db.add(coding_round)
        db.commit()

    # Record Audit & Activity Log
    audit = models.AuditLog(
        agent_name="Hiring Agent",
        action_type="EXECUTION",
        summary=f"Hiring Agent created position '{job.title}' with 20 MCQ questions and Coding assessment.",
        user_id=user_id
    )
    activity = models.AgentActivity(
        agent_name="Hiring Agent",
        action=f"Created hiring requisition: {job.title}",
        time="Just now",
        icon_type="Briefcase",
        bg_color="bg-emerald-500/10",
        user_id=user_id
    )
    db.add_all([audit, activity])
    db.commit()

    return {
        "message": "Job requisition and assessment pipeline created successfully",
        "job_id": job.id,
        "title": job.title,
        "mcq_count": len(mcq_list),
        "candidates_count": len(initial_cands)
    }

@router.get("/jobs")
def list_hiring_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).all()
    results = []
    for j in jobs:
        req_skills = []
        try:
            req_skills = json.loads(j.required_skills)
        except Exception:
            pass
        results.append({
            "id": j.id,
            "title": j.title,
            "department": j.department,
            "seniority": j.seniority,
            "target_compensation": j.target_compensation,
            "experience_years": j.experience_years,
            "required_skills": req_skills,
            "status": j.status,
            "candidates_count": len(j.candidates),
            "created_at": j.created_at.isoformat() if j.created_at else None
        })
    return results

@router.get("/jobs/{job_id}")
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    j = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")

    desc = {}
    try:
        desc = json.loads(j.job_description)
    except Exception:
        pass
    req_skills = []
    try:
        req_skills = json.loads(j.required_skills)
    except Exception:
        pass

    mcq_count = db.query(models.MCQQuestion).filter(models.MCQQuestion.job_id == job_id).count()
    coding_prob = db.query(models.CodingProblem).filter(models.CodingProblem.job_id == job_id).first()

    candidates_list = []
    for c in j.candidates:
        c_skills = []
        try:
            c_skills = json.loads(c.skills)
        except Exception:
            pass

        eval_data = None
        if c.evaluation:
            eval_data = {
                "overall_score": c.evaluation.overall_score,
                "resume_score": c.evaluation.resume_score,
                "mcq_score": c.evaluation.mcq_score,
                "coding_score": c.evaluation.coding_score,
                "recommendation": c.evaluation.recommendation,
                "founder_decision": c.evaluation.founder_decision
            }

        candidates_list.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "skills": c_skills,
            "experience_years": c.experience_years,
            "resume_match_score": c.resume_match_score,
            "status": c.status,
            "evaluation": eval_data
        })

    return {
        "id": j.id,
        "title": j.title,
        "department": j.department,
        "seniority": j.seniority,
        "target_compensation": j.target_compensation,
        "experience_years": j.experience_years,
        "required_skills": req_skills,
        "job_description": desc,
        "status": j.status,
        "mcq_questions_count": mcq_count,
        "has_coding_problem": coding_prob is not None,
        "candidates": candidates_list
    }

# -----------------------------------------------------------------
# 2. Candidate Screening Endpoints
# -----------------------------------------------------------------
@router.post("/jobs/{job_id}/candidates")
def add_and_screen_candidate(
    job_id: int,
    req: schemas.CandidateCreate,
    db: Session = Depends(get_db),
    current_user: Optional[Any] = Depends(auth.get_current_user_optional if hasattr(auth, "get_current_user_optional") else lambda: None)
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    user_id = current_user.id if current_user else None

    # Calculate Resume Match Score
    req_skills = json.loads(job.required_skills) if job.required_skills else []
    cand_skills = req.skills or []
    
    matched = set(s.lower() for s in cand_skills).intersection(set(s.lower() for s in req_skills))
    match_ratio = len(matched) / max(len(req_skills), 1)
    exp_factor = min(1.0, (req.experience_years or 0) / max(job.experience_years, 1))
    resume_score = round((match_ratio * 70.0 + exp_factor * 30.0), 1)
    
    status = "SHORTLISTED" if resume_score >= 60.0 else "REJECTED"

    cand = models.Candidate(
        job_id=job.id,
        user_id=user_id,
        name=req.name,
        email=req.email,
        resume_text=req.resume_text or f"{req.experience_years} years experience in {', '.join(cand_skills)}.",
        skills=json.dumps(cand_skills),
        experience_years=req.experience_years or 0,
        resume_match_score=resume_score,
        status=status
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    # Create Assessment Rounds
    mcq_count = db.query(models.MCQQuestion).filter(models.MCQQuestion.job_id == job_id).count()
    mcq_round = models.AssessmentRound(
        candidate_id=cand.id,
        job_id=job.id,
        round_type="MCQ",
        status="PENDING" if status == "SHORTLISTED" else "FAILED",
        duration_minutes=20,
        total_items=mcq_count or 20
    )
    coding_round = models.AssessmentRound(
        candidate_id=cand.id,
        job_id=job.id,
        round_type="CODING",
        status="PENDING",
        duration_minutes=30,
        total_items=1
    )
    db.add_all([mcq_round, coding_round])
    db.commit()

    # Log activity
    audit = models.AuditLog(
        agent_name="Hiring Agent",
        action_type="EXECUTION",
        summary=f"Hiring Agent screened {cand.name} for '{job.title}'. Match Score: {resume_score}%. Status: {status}.",
        user_id=user_id
    )
    db.add(audit)
    db.commit()

    return {
        "candidate_id": cand.id,
        "name": cand.name,
        "resume_match_score": resume_score,
        "status": status,
        "message": "Candidate screened & added to pipeline"
    }

@router.get("/candidates/{candidate_id}")
def get_candidate_detail(candidate_id: int, db: Session = Depends(get_db)):
    cand = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = cand.job
    skills = json.loads(cand.skills) if cand.skills else []

    rounds = []
    for r in cand.assessments:
        rounds.append({
            "assessment_id": r.id,
            "round_type": r.round_type,
            "status": r.status,
            "score": r.score,
            "duration_minutes": r.duration_minutes,
            "total_items": r.total_items,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None
        })

    eval_data = None
    if cand.evaluation:
        strengths = json.loads(cand.evaluation.strengths) if cand.evaluation.strengths else []
        concerns = json.loads(cand.evaluation.concerns) if cand.evaluation.concerns else []
        eval_data = {
            "resume_score": cand.evaluation.resume_score,
            "mcq_score": cand.evaluation.mcq_score,
            "coding_score": cand.evaluation.coding_score,
            "overall_score": cand.evaluation.overall_score,
            "recommendation": cand.evaluation.recommendation,
            "strengths": strengths,
            "concerns": concerns,
            "founder_decision": cand.evaluation.founder_decision,
            "decision_notes": cand.evaluation.decision_notes
        }

    return {
        "id": cand.id,
        "job_id": cand.job_id,
        "job_title": job.title if job else "",
        "name": cand.name,
        "email": cand.email,
        "resume_text": cand.resume_text,
        "skills": skills,
        "experience_years": cand.experience_years,
        "resume_match_score": cand.resume_match_score,
        "status": cand.status,
        "assessment_rounds": rounds,
        "evaluation": eval_data,
        "created_at": cand.created_at.isoformat() if cand.created_at else None
    }

# -----------------------------------------------------------------
# 3. Candidate Assessment Loading Endpoints
# -----------------------------------------------------------------
@router.get("/assessment/{assessment_id}")
def load_candidate_assessment(assessment_id: int, db: Session = Depends(get_db)):
    r = db.query(models.AssessmentRound).filter(models.AssessmentRound.id == assessment_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Assessment round not found")

    cand = r.candidate
    job = r.job

    if r.round_type == "MCQ":
        questions = db.query(models.MCQQuestion).filter(models.MCQQuestion.job_id == r.job_id).all()
        q_payload = []
        for q in questions:
            opts = json.loads(q.options) if q.options else []
            # Note: Do NOT return correct_option_index during active test taking
            q_payload.append({
                "id": q.id,
                "question_text": q.question_text,
                "options": opts,
                "topic": q.topic,
                "difficulty": q.difficulty
            })
        return {
            "assessment_id": r.id,
            "candidate_id": cand.id,
            "candidate_name": cand.name,
            "job_title": job.title,
            "round_type": "MCQ",
            "duration_minutes": r.duration_minutes,
            "total_questions": len(q_payload),
            "questions": q_payload,
            "status": r.status
        }
    else:
        # Coding Round
        coding_prob = db.query(models.CodingProblem).filter(models.CodingProblem.job_id == r.job_id).first()
        if not coding_prob:
            raise HTTPException(status_code=404, detail="Coding problem not found")

        examples = json.loads(coding_prob.examples) if coding_prob.examples else []
        constraints = json.loads(coding_prob.constraints) if coding_prob.constraints else []
        starter_code = json.loads(coding_prob.starter_code) if coding_prob.starter_code else {}

        return {
            "assessment_id": r.id,
            "candidate_id": cand.id,
            "candidate_name": cand.name,
            "job_title": job.title,
            "round_type": "CODING",
            "problem": {
                "id": coding_prob.id,
                "title": coding_prob.title,
                "description": coding_prob.description,
                "difficulty": coding_prob.difficulty,
                "time_limit_mins": coding_prob.time_limit_mins,
                "examples": examples,
                "constraints": constraints,
                "starter_code": starter_code
            },
            "status": r.status
        }

# -----------------------------------------------------------------
# 4. Round 1 — MCQ Submission Endpoint
# -----------------------------------------------------------------
@router.post("/assessment/{assessment_id}/mcq/submit")
def submit_mcq_answers(
    assessment_id: int,
    req: schemas.MCQSubmitRequest,
    db: Session = Depends(get_db)
):
    r = db.query(models.AssessmentRound).filter(models.AssessmentRound.id == assessment_id).first()
    if not r or r.round_type != "MCQ":
        raise HTTPException(status_code=404, detail="MCQ Assessment not found")

    questions = db.query(models.MCQQuestion).filter(models.MCQQuestion.job_id == r.job_id).all()
    q_map = {q.id: q for q in questions}

    correct_count = 0
    total_count = len(req.answers)
    topic_scores = {}

    for ans in req.answers:
        q = q_map.get(ans.question_id)
        if not q:
            continue

        is_corr = (ans.selected_option_index == q.correct_option_index)
        if is_corr:
            correct_count += 1

        topic = q.topic or "General"
        if topic not in topic_scores:
            topic_scores[topic] = {"correct": 0, "total": 0}
        topic_scores[topic]["total"] += 1
        if is_corr:
            topic_scores[topic]["correct"] += 1

        # Record answer
        ans_rec = models.CandidateMCQAnswer(
            assessment_id=r.id,
            candidate_id=r.candidate_id,
            question_id=q.id,
            selected_option_index=ans.selected_option_index,
            is_correct=is_corr
        )
        db.add(ans_rec)

    mcq_score = round((correct_count / max(total_count, 1)) * 100, 1)
    r.score = mcq_score
    r.status = "COMPLETED"
    r.completed_at = datetime.utcnow()

    # Update candidate status
    cand = r.candidate
    is_passed = mcq_score >= 60.0
    cand.status = "CODING_PENDING" if is_passed else "REJECTED"
    db.commit()

    # Record Activity & Audit
    audit = models.AuditLog(
        agent_name="Hiring Agent",
        action_type="EXECUTION",
        summary=f"Candidate {cand.name} completed Round 1 MCQ ({mcq_score}%). Status: {'Passed to Coding Round' if is_passed else 'Rejected'}.",
        user_id=cand.user_id
    )
    db.add(audit)
    db.commit()

    return {
        "assessment_id": r.id,
        "score": mcq_score,
        "correct_count": correct_count,
        "total_count": total_count,
        "is_passed": is_passed,
        "next_status": cand.status,
        "topic_breakdown": topic_scores
    }

# -----------------------------------------------------------------
# 5. Round 2 — Coding Execution & Submission Endpoints
# -----------------------------------------------------------------
@router.post("/assessment/{assessment_id}/coding/run")
def run_coding_test_cases(
    assessment_id: int,
    req: schemas.CodingRunRequest,
    db: Session = Depends(get_db)
):
    r = db.query(models.AssessmentRound).filter(models.AssessmentRound.id == assessment_id).first()
    if not r or r.round_type != "CODING":
        raise HTTPException(status_code=404, detail="Coding Assessment not found")

    prob = db.query(models.CodingProblem).filter(models.CodingProblem.job_id == r.job_id).first()
    if not prob:
        raise HTTPException(status_code=404, detail="Coding problem not found")

    test_cases = json.loads(prob.test_cases) if prob.test_cases else []
    eval_res = CodeExecutor.evaluate_submission(req.language or "python", req.code, test_cases)
    return eval_res

@router.post("/assessment/{assessment_id}/coding/submit")
def submit_coding_solution(
    assessment_id: int,
    req: schemas.CodingSubmitRequest,
    db: Session = Depends(get_db)
):
    r = db.query(models.AssessmentRound).filter(models.AssessmentRound.id == assessment_id).first()
    if not r or r.round_type != "CODING":
        raise HTTPException(status_code=404, detail="Coding Assessment not found")

    prob = db.query(models.CodingProblem).filter(models.CodingProblem.job_id == r.job_id).first()
    if not prob:
        raise HTTPException(status_code=404, detail="Coding problem not found")

    test_cases = json.loads(prob.test_cases) if prob.test_cases else []
    eval_res = CodeExecutor.evaluate_submission(req.language or "python", req.code, test_cases)

    sub = models.CodingSubmission(
        assessment_id=r.id,
        candidate_id=r.candidate_id,
        problem_id=prob.id,
        language=req.language or "python",
        code=req.code,
        test_cases_passed=eval_res.get("test_cases_passed", 0),
        total_test_cases=eval_res.get("total_test_cases", 0),
        status=eval_res.get("status", "COMPLETED"),
        execution_time_ms=eval_res.get("execution_time_ms", 0)
    )
    db.add(sub)

    coding_score = eval_res.get("pass_rate_percent", 0.0)
    r.score = coding_score
    r.status = "COMPLETED"
    r.completed_at = datetime.utcnow()

    cand = r.candidate
    cand.status = "UNDER_REVIEW"
    db.commit()

    # Generate Candidate Evaluation & AI Recommendation
    mcq_round = db.query(models.AssessmentRound).filter(
        models.AssessmentRound.candidate_id == cand.id,
        models.AssessmentRound.round_type == "MCQ"
    ).first()
    mcq_score = mcq_round.score if mcq_round else 80.0

    eval_summary = hiring_agent.generate_candidate_evaluation(
        candidate_name=cand.name,
        resume_score=cand.resume_match_score,
        mcq_score=mcq_score,
        coding_score=coding_score,
        resume_weight=0.20,
        mcq_weight=0.30,
        coding_weight=0.50
    )

    cand_eval = models.CandidateEvaluation(
        candidate_id=cand.id,
        job_id=cand.job_id,
        resume_score=cand.resume_match_score,
        mcq_score=mcq_score,
        coding_score=coding_score,
        resume_weight=0.20,
        mcq_weight=0.30,
        coding_weight=0.50,
        overall_score=eval_summary.get("overall_score", 85.0),
        recommendation=eval_summary.get("recommendation", "STRONG_HIRE"),
        strengths=json.dumps(eval_summary.get("strengths", [])),
        concerns=json.dumps(eval_summary.get("concerns", [])),
        founder_decision="PENDING"
    )
    db.add(cand_eval)
    cand.status = "RECOMMENDED"
    db.commit()

    # Activity & Audit
    audit = models.AuditLog(
        agent_name="Hiring Agent",
        action_type="EXECUTION",
        summary=f"Candidate {cand.name} completed Coding Round ({coding_score}%). Overall Score: {eval_summary.get('overall_score')}% -> Recommendation: {eval_summary.get('recommendation')}.",
        user_id=cand.user_id
    )
    db.add(audit)
    db.commit()

    return {
        "assessment_id": r.id,
        "coding_score": coding_score,
        "evaluation": eval_summary
    }

# -----------------------------------------------------------------
# 6. Candidate Comparison Matrix Endpoint
# -----------------------------------------------------------------
@router.get("/jobs/{job_id}/comparison")
def get_candidate_comparison_matrix(job_id: int, db: Session = Depends(get_db)):
    candidates = db.query(models.Candidate).filter(models.Candidate.job_id == job_id).all()
    matrix = []
    for c in candidates:
        mcq_round = db.query(models.AssessmentRound).filter(models.AssessmentRound.candidate_id == c.id, models.AssessmentRound.round_type == "MCQ").first()
        coding_round = db.query(models.AssessmentRound).filter(models.AssessmentRound.candidate_id == c.id, models.AssessmentRound.round_type == "CODING").first()

        mcq_score = mcq_round.score if mcq_round and mcq_round.status == "COMPLETED" else None
        coding_score = coding_round.score if coding_round and coding_round.status == "COMPLETED" else None

        overall = c.evaluation.overall_score if c.evaluation else None
        rec = c.evaluation.recommendation if c.evaluation else "PENDING"
        decision = c.evaluation.founder_decision if c.evaluation else "PENDING"

        matrix.append({
            "candidate_id": c.id,
            "name": c.name,
            "email": c.email,
            "resume_match": c.resume_match_score,
            "mcq_score": mcq_score,
            "coding_score": coding_score,
            "overall_score": overall,
            "status": c.status,
            "recommendation": rec,
            "founder_decision": decision
        })

    # Sort matrix by overall score desc
    matrix.sort(key=lambda x: (x["overall_score"] or 0), reverse=True)
    return matrix

# -----------------------------------------------------------------
# 7. Founder Approval Gate Endpoint
# -----------------------------------------------------------------
@router.post("/candidates/{candidate_id}/decision")
def record_founder_hiring_decision(
    candidate_id: int,
    req: schemas.FounderDecisionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Any] = Depends(auth.get_current_user_optional if hasattr(auth, "get_current_user_optional") else lambda: None)
):
    cand = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    user_id = current_user.id if current_user else None

    if not cand.evaluation:
        cand_eval = models.CandidateEvaluation(
            candidate_id=cand.id,
            job_id=cand.job_id,
            founder_decision=req.decision,
            decision_notes=req.notes
        )
        db.add(cand_eval)
    else:
        cand.evaluation.founder_decision = req.decision
        cand.evaluation.decision_notes = req.notes

    if req.decision == "APPROVED":
        cand.status = "APPROVED"
    elif req.decision == "REJECTED":
        cand.status = "REJECTED"
    else:
        cand.status = "UNDER_REVIEW"

    db.commit()

    # Log Audit & Activity
    audit = models.AuditLog(
        agent_name="Hiring Agent",
        action_type="APPROVAL",
        summary=f"Founder decision for {cand.name}: {req.decision}.",
        user_id=user_id
    )
    activity = models.AgentActivity(
        agent_name="Hiring Agent",
        action=f"Founder {req.decision} candidate {cand.name}",
        time="Just now",
        icon_type="CheckCircle2",
        bg_color="bg-emerald-500/10",
        user_id=user_id
    )
    db.add_all([audit, activity])
    db.commit()

    return {
        "candidate_id": cand.id,
        "name": cand.name,
        "founder_decision": req.decision,
        "status": cand.status,
        "message": f"Founder decision '{req.decision}' recorded successfully."
    }
