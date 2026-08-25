import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

import models
import schemas
from adapters import MockFinanceService, MockSocialAdapter, MockCandidateRepository, MockDocumentService

class CEOOrchestrator:
    @staticmethod
    def extract_entities(title: str) -> Dict[str, Any]:
        lower = title.lower()
        
        # Budget
        budget_match = re.search(r'(\$[\d,]+k?|\b\d+\s*k\b|₹[\d,]+|\b\d+\s*lakhs?\b|budget\s*(?:of|is|:)?\s*[\$\₹\w\d,]+)', title, re.IGNORECASE)
        budget = budget_match.group(0) if budget_match else "Standard Operating Budget"
        
        # Experience
        exp_match = re.search(r'(\d+\+?\s*(?:years?|yrs?)(?:\s+of)?\s*(?:experience|exp)?)', title, re.IGNORECASE)
        experience = exp_match.group(0) if exp_match else "3+ years relevant domain expertise"
        
        # Role
        role = "Frontend Developer"
        roles = [
            "senior frontend engineer", "senior backend engineer", "frontend engineer", "frontend developer",
            "backend engineer", "backend developer", "full stack developer", "full stack engineer",
            "software engineer", "product manager", "ui/ux designer", "marketing manager",
            "growth marketer", "sales executive", "data scientist", "devops engineer"
        ]
        for r in roles:
            if r in lower:
                role = r.title()
                break
                
        # Intent flags
        is_hiring = any(k in lower for k in ["hire", "hiring", "engineer", "developer", "designer", "recruitment", "talent", "candidate", "sde"])
        is_office_lease = any(k in lower for k in ["office", "lease", "rent", "facility", "workspace", "real estate", "coworking", "afford a new office"])
        is_marketing = any(k in lower for k in ["market", "marketing", "launch", "campaign", "ad", "growth", "seo", "social", "branding", "strategy for our product"])
        is_fundraising = any(k in lower for k in ["fund", "investor", "pitch", "raise", "seed", "safe", "venture", "pre-seed"])
        is_research = any(k in lower for k in ["research", "competitor", "pricing model", "analysis", "benchmark", "survey"])

        return {
            "title": title,
            "role": role,
            "budget": budget,
            "experience": experience,
            "is_hiring": is_hiring,
            "is_office_lease": is_office_lease,
            "is_marketing": is_marketing,
            "is_fundraising": is_fundraising,
            "is_research": is_research
        }

    @classmethod
    def decompose_task(cls, title: str) -> schemas.CEOPlan:
        """
        Dynamically analyzes the objective, selects ONLY required agents,
        establishes dependencies and execution order, and builds the plan.
        """
        ent = cls.extract_entities(title)
        
        if ent["is_hiring"]:
            # Hiring workflow: Finance -> Marketing -> Hiring -> Legal (Startup Intern Tier: Max ₹10k/mo)
            intern_role = ent['role'] if "intern" in ent['role'].lower() else f"{ent['role']} Intern"
            return schemas.CEOPlan(
                goal=f"Hire a {intern_role} (Budget: <= ₹10,000 / month)",
                analysis=[
                    "Validate startup cash reserves and enforce strict intern stipend limit (max ₹10k/month)",
                    f"Formulate {intern_role} job description & high-engagement recruitment campaign",
                    "Collect candidate applications, screen GitHub portfolios, and rank top intern candidates",
                    "Conduct structured founder interview & select top candidate",
                    "Draft formal Internship Offer Letter & 100% IP Assignment Agreement"
                ],
                required_agents=["Finance", "Marketing", "Hiring", "Legal"],
                skipped_agents=["Sales", "Operations", "Research"],
                execution_steps=[
                    schemas.CEOPlanStep(
                        order=1,
                        agent="Finance",
                        responsibility=f"Model {intern_role} stipend budget (capped at max ₹10,000 / month) and confirm runway burn impact.",
                        dependencies=[],
                        required_inputs=["Startup cash reserve data", "Intern stipend benchmarks (₹8k–₹10k/mo)"],
                        expected_output="Approved intern stipend ceiling & runway safety confirmation",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=2,
                        agent="Marketing",
                        responsibility="Create recruitment campaign, formatted LinkedIn post, and Telegram broadcast with approved intern stipend and PPO opportunity.",
                        dependencies=["Finance"],
                        required_inputs=["Approved stipend range from Finance Agent"],
                        expected_output="High-converting intern job post copies with 1-click publish",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=3,
                        agent="Hiring",
                        responsibility=f"Source & screen candidates, evaluate GitHub projects, and rank top intern applicants for founder review.",
                        dependencies=["Marketing"],
                        required_inputs=["Published recruitment campaign & candidate pipeline"],
                        expected_output="Ranked intern leaderboard with match scores and interview recommendations",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=4,
                        agent="Legal",
                        responsibility=f"Draft formal Internship Offer Letter & 100% IP Assignment Agreement for the selected candidate.",
                        dependencies=["Hiring"],
                        required_inputs=["Selected candidate details & Finance stipend terms"],
                        expected_output="Legally compliant internship offer letter with digital dispatch authorization",
                        approval_required=True
                    )
                ],
                risks=[
                    "Candidate availability if college examinations coincide with start date",
                    "Need mentor guidance for onboarding within the first 2 weeks"
                ],
                budget_estimate="₹10,000 / month max (₹30,000 for 3-month term)",
                recommended_order=["Finance", "Marketing", "Hiring", "Legal"]
            )
            
        elif ent["is_office_lease"]:
            # Office Lease workflow: Finance -> Operations -> Legal (NO Marketing, NO Hiring!)
            return schemas.CEOPlan(
                goal=f"Assess & Secure New Office Facility ({ent['budget']})",
                analysis=[
                    "Audit financial reserves, security deposit capacity & recurring rent affordability",
                    "Review commercial lease term sheets, lock-in period & landlord covenants",
                    "Evaluate facility specs (high-speed connectivity, workstations, meeting zones)"
                ],
                required_agents=["Finance", "Operations", "Legal"],
                skipped_agents=["Marketing", "Hiring", "Sales", "Research"],
                execution_steps=[
                    schemas.CEOPlanStep(
                        order=1,
                        agent="Finance",
                        responsibility="Model commercial rent cash flow, calculate 3-month deposit impact, and verify minimum 12-month runway buffer.",
                        dependencies=[],
                        required_inputs=["Current cash reserves", "Proposed monthly lease cost"],
                        expected_output="Lease affordability assessment and maximum deposit ceiling",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=2,
                        agent="Operations",
                        responsibility="Verify office space requirements (15-20 workstations, dedicated fiber internet, HVAC, power backup).",
                        dependencies=["Finance"],
                        required_inputs=["Approved space budget & headcount growth projections"],
                        expected_output="Facility operational specification & setup budget",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=3,
                        agent="Legal",
                        responsibility="Review standard commercial lease agreement, negotiate lock-in clauses, and verify landlord title compliance.",
                        dependencies=["Operations"],
                        required_inputs=["Operations facility specs & Finance deposit terms"],
                        expected_output="Commercial lease contract summary and signing recommendation",
                        approval_required=True
                    )
                ],
                risks=[
                    "Long-term lock-in period without sublease flexibility",
                    "Escalation clauses exceeding 5% annual inflation"
                ],
                budget_estimate=ent["budget"],
                recommended_order=["Finance", "Operations", "Legal"]
            )

        elif ent["is_marketing"]:
            # Marketing Launch workflow: Marketing -> Finance -> Legal (NO Hiring!)
            return schemas.CEOPlan(
                goal="Launch Go-To-Market & Growth Strategy",
                analysis=[
                    "Architect multi-channel growth narrative across LinkedIn, Twitter & Product Hunt",
                    "Model Customer Acquisition Cost (CAC), Return on Ad Spend (ROAS), and ad spend limits",
                    "Ensure advertising disclosures, GDPR privacy compliance & terms of service"
                ],
                required_agents=["Marketing", "Finance", "Legal"],
                skipped_agents=["Hiring", "Operations", "Sales"],
                execution_steps=[
                    schemas.CEOPlanStep(
                        order=1,
                        agent="Marketing",
                        responsibility="Develop viral launch hooks, founder announcement threads, and community outreach playbook.",
                        dependencies=[],
                        required_inputs=["Product value proposition", "Target founder persona"],
                        expected_output="Complete multi-platform launch collateral with publish hooks",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=2,
                        agent="Finance",
                        responsibility="Allocate paid acquisition budget, define $45 target CAC, and set daily ad spend caps.",
                        dependencies=["Marketing"],
                        required_inputs=["Marketing campaign channels & budget bounds"],
                        expected_output="Unit economics CAC / LTV model and burn limits",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=3,
                        agent="Legal",
                        responsibility="Review marketing promotional claims, disclaimers, and data protection privacy policies.",
                        dependencies=["Marketing"],
                        required_inputs=["Marketing campaign copy & promotional assets"],
                        expected_output="Regulatory compliance certification and consent terms",
                        approval_required=True
                    )
                ],
                risks=[
                    "Ad fatigue in saturated digital distribution channels",
                    "Conversion bottleneck on target landing page"
                ],
                budget_estimate=ent["budget"],
                recommended_order=["Marketing", "Finance", "Legal"]
            )
            
        else:
            # General Strategic Objective: Dynamic multi-department
            return schemas.CEOPlan(
                goal=f"Execute: {title[:60]}",
                analysis=[
                    "Decompose high-level founder directive into departmental workstreams",
                    "Allocate required financial & operational resources",
                    "Verify regulatory compliance and risk mitigations"
                ],
                required_agents=["Finance", "Marketing", "Legal"],
                skipped_agents=["Hiring", "Operations", "Sales", "Research"],
                execution_steps=[
                    schemas.CEOPlanStep(
                        order=1,
                        agent="Finance",
                        responsibility=f"Structure capital allocation and ROI model for '{title[:50]}'.",
                        dependencies=[],
                        required_inputs=["Objective parameters"],
                        expected_output="Financial feasibility & resource plan",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=2,
                        agent="Marketing",
                        responsibility="Draft internal and external stakeholder communications plan.",
                        dependencies=["Finance"],
                        required_inputs=["Approved financial terms"],
                        expected_output="Stakeholder communication collateral",
                        approval_required=True
                    ),
                    schemas.CEOPlanStep(
                        order=3,
                        agent="Legal",
                        responsibility="Conduct regulatory assessment and prepare necessary agreements.",
                        dependencies=["Finance"],
                        required_inputs=["Project scope"],
                        expected_output="Legal review and risk mitigation",
                        approval_required=True
                    )
                ],
                risks=["Scope changes during execution phase"],
                budget_estimate=ent["budget"],
                recommended_order=["Finance", "Marketing", "Legal"]
            )

    @classmethod
    def setup_task_workflow(cls, task: models.Task, db: Session, user_id: int):
        """
        Creates the CEO plan and populates initial Delegations.
        """
        plan = cls.decompose_task(task.title)
        task.plan_data = json.dumps(plan.model_dump())
        task.status = "AWAITING_PLAN_APPROVAL"
        task.progress = 0
        task.summary = f"CEO Agent formulated an execution plan with {len(plan.required_agents)} agents: {', '.join(plan.required_agents)}."

        # Clear existing delegations if any
        db.query(models.Delegation).filter(models.Delegation.task_id == task.id).delete()

        now_str = datetime.now().strftime("%I:%M %p")

        for step in plan.execution_steps:
            del_model = models.Delegation(
                agent=step.agent,
                task_description=step.responsibility,
                status="BLOCKED",
                order_index=step.order,
                dependencies=json.dumps(step.dependencies),
                context_input=json.dumps({"required_inputs": step.required_inputs, "expected_output": step.expected_output}),
                result_output="{}",
                actions_available="[]",
                actions_taken="[]",
                task_id=task.id,
                user_id=user_id
            )
            db.add(del_model)

        # Record CEO activity
        activity = models.AgentActivity(
            agent_name="CEO Agent",
            action=f"Formulated execution plan for '{task.title[:50]}...'",
            time=now_str,
            icon_type="briefcase",
            bg_color="bg-[#8B5CF6]/15",
            user_id=user_id
        )
        db.add(activity)

        # Record AuditLog
        audit = models.AuditLog(
            task_id=task.id,
            agent_name="CEO Agent",
            action_type="ORCHESTRATION",
            summary=f"Task created and decomposed into {len(plan.required_agents)} agent workstreams.",
            details=json.dumps({"required_agents": plan.required_agents, "skipped_agents": plan.skipped_agents}),
            user_id=user_id
        )
        db.add(audit)

        db.commit()
        db.refresh(task)
        return task

    @classmethod
    def approve_plan(cls, task: models.Task, db: Session, user_id: int, decision: str = "APPROVED", feedback: str = None):
        """
        Level A Approval: Founder approves the CEO's overall execution plan.
        Unlocks the initial unblocked agent task(s) to 'READY'.
        """
        if decision == "REJECTED":
            task.status = "REJECTED"
            db.commit()
            return task

        task.status = "APPROVED"
        task.progress = 10

        # Record Approval
        appr = models.Approval(
            title=f"CEO Plan Approval: {task.title[:50]}",
            approval_level="PLAN_APPROVAL",
            action_name="Approve CEO Plan",
            decision="APPROVED",
            feedback=feedback,
            task_id=task.id,
            user_id=user_id
        )
        db.add(appr)

        # Find delegations with empty dependencies and set them to READY
        for del_item in task.delegations:
            deps = json.loads(del_item.dependencies or "[]")
            if len(deps) == 0:
                del_item.status = "READY"
            else:
                del_item.status = "BLOCKED"

        audit = models.AuditLog(
            task_id=task.id,
            agent_name="Founder",
            action_type="APPROVAL",
            summary=f"Founder approved the CEO Execution Plan for '{task.title[:50]}'. Initial tasks unlocked.",
            details=json.dumps({"feedback": feedback}),
            user_id=user_id
        )
        db.add(audit)

        db.commit()
        db.refresh(task)
        return task

    @classmethod
    def execute_agent_task(cls, delegation: models.Delegation, db: Session, user_id: int):
        """
        Executes the agent task upon founder clicking START TASK.
        Gathers upstream inputs via CEO state and generates structured outputs.
        """
        task = delegation.task
        ent = cls.extract_entities(task.title)
        agent = delegation.agent

        delegation.status = "RUNNING"
        db.commit()

        # Collect upstream outputs from previous completed delegations
        upstream_outputs = {}
        for d in task.delegations:
            if d.id != delegation.id and d.status == "COMPLETED" and d.result_output:
                try:
                    upstream_outputs[d.agent] = json.loads(d.result_output)
                except:
                    pass

        result = {}
        decision_summary = ""
        actions_available = []

        if agent == "Finance":
            if ent["is_hiring"]:
                fin_data = MockFinanceService.analyze_hiring_budget(ent["role"], ent["budget"])
                result = fin_data
                decision_summary = f"Assessed startup runway (>24 mos). Approved intern stipend budget of {fin_data['salary_range']} (capped at <= ₹10,000/mo). Monthly burn increases by only {fin_data['monthly_burn_increase']}."
                actions_available = []
            elif ent["is_office_lease"]:
                fin_data = MockFinanceService.analyze_office_lease(ent["budget"])
                result = fin_data
                decision_summary = f"Verified cash reserves. Approved {fin_data['facility_budget']} rent and {fin_data['security_deposit_required']} security deposit."
                actions_available = [
                    {"id": "authorize_lease_deposit", "name": "APPROVE SECURITY DEPOSIT RELEASE", "consequential": True}
                ]
            else:
                fin_data = MockFinanceService.analyze_marketing_budget(ent["budget"])
                result = fin_data
                decision_summary = f"Configured {fin_data['total_campaign_budget']} spend cap with target CAC of {fin_data['target_cac']}."
                actions_available = [
                    {"id": "authorize_ad_budget", "name": "AUTHORIZE MARKETING AD-SPEND", "consequential": True}
                ]

        elif agent == "Marketing":
            salary_info = upstream_outputs.get("Finance", {}).get("salary_range", "₹8,000 – ₹10,000 / month")
            if ent["is_hiring"]:
                posts = MockSocialAdapter.generate_recruitment_posts(ent["role"], salary_info, ent["experience"])
                result = posts
                decision_summary = f"Drafted high-converting startup intern recruitment campaign for LinkedIn and Telegram with {salary_info} stipend and PPO opportunity."
                actions_available = [
                    {"id": "publish_linkedin", "name": "APPROVE & POST TO LINKEDIN", "consequential": True, "target": "LinkedIn"},
                    {"id": "publish_telegram", "name": "APPROVE & POST TO TELEGRAM", "consequential": True, "target": "Telegram"}
                ]
            else:
                posts = MockSocialAdapter.generate_recruitment_posts(ent["title"][:40], "High ROI Campaign", "Product Launch")
                result = posts
                decision_summary = "Crafted multi-channel launch announcement copy and social media distribution threads."
                actions_available = [
                    {"id": "publish_linkedin", "name": "APPROVE & PUBLISH ANNOUNCEMENT", "consequential": True, "target": "LinkedIn"}
                ]

        elif agent == "Hiring":
            salary_band = upstream_outputs.get("Finance", {}).get("salary_range", "₹8,000 – ₹10,000 / month")
            candidates = MockCandidateRepository.screen_and_rank_candidates(ent["role"], ent["experience"], salary_band)
            result = {"candidates": candidates, "role": ent["role"], "total_screened": 42, "recommended_for_interview": 2}
            top_cand = candidates[0]["name"] if candidates else "Rahul Sharma"
            decision_summary = f"Screened 42 student & fresher applicants within <= ₹10k/mo stipend. Ranked {len(candidates)} shortlisted candidates. Top candidate {top_cand} scored 94% match."
            actions_available = [
                {"id": "select_candidate_rahul", "name": f"APPROVE & SELECT {top_cand} FOR INTERNSHIP OFFER", "consequential": True, "candidate_name": top_cand},
                {"id": "schedule_interviews", "name": "DISPATCH CALENDAR INVITES", "consequential": False}
            ]

            # Ensure Job & Candidate models are created in DB for frontend pipeline integration
            try:
                existing_job = db.query(models.Job).filter(models.Job.task_id == task.id).first()
                if not existing_job:
                    from agent_system.gemini_client import GeminiClient
                    from agent_system.agents.hiring_agent import HiringAgent as HA
                    ha_instance = HA(GeminiClient())
                    
                    job = models.Job(
                        user_id=user_id,
                        task_id=task.id,
                        title=ent["role"],
                        department="Engineering",
                        seniority="Mid-Level",
                        target_compensation=salary_band,
                        required_skills=json.dumps(["React", "JavaScript", "TypeScript", "Python"]),
                        experience_years=2,
                        status="OPEN"
                    )
                    db.add(job)
                    db.commit()
                    db.refresh(job)

                    mcq_list = ha_instance.generate_mcq_questions(job.title, ["React", "JavaScript", "TypeScript", "Python"], count=20)
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

                    coding_prob = ha_instance.generate_coding_problem(job.title, ["Python", "JavaScript"])
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

                    for cand_item in candidates:
                        cand_rec = models.Candidate(
                            job_id=job.id,
                            user_id=user_id,
                            name=cand_item.get("name", "Rahul Sharma"),
                            email=f"{cand_item.get('name', 'rahul').lower().replace(' ', '.')}@example.com",
                            resume_text=f"Experienced in {cand_item.get('skills', ['React'])}. {cand_item.get('experience', '2 years exp')}.",
                            skills=json.dumps(cand_item.get("skills", ["React", "JavaScript"])),
                            experience_years=2,
                            resume_match_score=float(cand_item.get("match_score", 90.0)),
                            status="SHORTLISTED"
                        )
                        db.add(cand_rec)
                        db.commit()
                        db.refresh(cand_rec)

                        mcq_round = models.AssessmentRound(
                            candidate_id=cand_rec.id,
                            job_id=job.id,
                            round_type="MCQ",
                            status="PENDING",
                            duration_minutes=20,
                            total_items=len(mcq_list)
                        )
                        coding_round = models.AssessmentRound(
                            candidate_id=cand_rec.id,
                            job_id=job.id,
                            round_type="CODING",
                            status="PENDING",
                            duration_minutes=30,
                            total_items=1
                        )
                        db.add_all([mcq_round, coding_round])
                        db.commit()
            except Exception as e:
                print(f"Hiring Agent DB Sync Note: {e}")

        elif agent == "Legal":
            cand_name = "Rahul Sharma"
            if "Hiring" in upstream_outputs and "candidates" in upstream_outputs["Hiring"]:
                cands = upstream_outputs["Hiring"]["candidates"]
                if len(cands) > 0:
                    cand_name = cands[0]["name"]

            salary_val = upstream_outputs.get("Finance", {}).get("constraints_for_downstream", {}).get("max_salary", "₹10,000 / month")
            doc = MockDocumentService.generate_offer_letter(cand_name, ent["role"], salary_val)
            result = doc
            decision_summary = f"Generated binding Internship Offer & Engagement Letter for {cand_name} ({salary_val}) with 100% IP Assignment and NDA covenants."
            actions_available = [
                {"id": "send_offer_letter", "name": f"APPROVE & SEND INTERN OFFER TO {cand_name}", "consequential": True, "candidate_name": cand_name, "document_id": doc["document_id"]},
                {"id": "download_offer_pdf", "name": "DOWNLOAD DRAFT PDF", "consequential": False}
            ]

        elif agent == "Operations":
            result = {
                "workstations": "20 dedicated ergonomic setups",
                "internet": "Primary 1Gbps Fiber + 500Mbps redundant backup",
                "security": "Biometric access control + CCTV infrastructure",
                "setup_timeline": "10 business days post lease signing",
                "status": "Ready for Execution"
            }
            decision_summary = "Prepared complete facility layout, IT hardware configuration, and utilities onboarding plan."
            actions_available = [
                {"id": "approve_ops_setup", "name": "AUTHORIZE HARDWARE ORDER", "consequential": True}
            ]

        else:
            result = {"summary": f"Completed domain analysis for {agent} Agent.", "status": "Ready"}
            decision_summary = f"{agent} Agent completed requirements analysis and prepared deliverable."
            actions_available = []

        delegation.decision_summary = decision_summary
        delegation.result_output = json.dumps(result)
        delegation.actions_available = json.dumps(actions_available)
        delegation.status = "AWAITING_APPROVAL"

        # Log audit
        audit = models.AuditLog(
            task_id=task.id,
            agent_name=f"{agent} Agent",
            action_type="EXECUTION",
            summary=f"{agent} Agent executed task and generated structured deliverable. Awaiting founder review.",
            details=json.dumps({"decision_summary": decision_summary}),
            user_id=user_id
        )
        db.add(audit)

        db.commit()
        db.refresh(delegation)
        return delegation

    @classmethod
    def approve_agent_result(cls, delegation: models.Delegation, db: Session, user_id: int, feedback: str = None):
        """
        Level B Approval: Founder approves the agent's generated result.
        Marks delegation COMPLETED, recalculates progress, and unblocks downstream tasks!
        """
        task = delegation.task
        delegation.status = "COMPLETED"
        delegation.approved_at = datetime.utcnow()

        # Record Approval
        appr = models.Approval(
            title=f"Result Approval: {delegation.agent} Agent",
            approval_level="RESULT_APPROVAL",
            action_name=f"Approve {delegation.agent} Result",
            decision="APPROVED",
            feedback=feedback,
            task_id=task.id,
            delegation_id=delegation.id,
            user_id=user_id
        )
        db.add(appr)

        # Check all other delegations to unlock next dependent tasks
        completed_agents = {d.agent for d in task.delegations if d.status == "COMPLETED" or d.id == delegation.id}
        
        for d in task.delegations:
            if d.id != delegation.id and d.status == "BLOCKED":
                deps = json.loads(d.dependencies or "[]")
                # If all dependencies are in completed_agents, unlock to READY!
                if all(dep in completed_agents for dep in deps):
                    d.status = "READY"

        # Recalculate task progress
        total_dels = len(task.delegations)
        comp_dels = sum(1 for d in task.delegations if d.status == "COMPLETED" or d.id == delegation.id)
        
        if total_dels > 0:
            task.progress = int((comp_dels / total_dels) * 90) + 10

        if comp_dels == total_dels:
            task.status = "COMPLETED"
            task.progress = 100

        audit = models.AuditLog(
            task_id=task.id,
            agent_name=f"{delegation.agent} Agent",
            action_type="APPROVAL",
            summary=f"Founder approved {delegation.agent} Agent result. Downstream dependencies evaluated.",
            details=json.dumps({"completed_agents": list(completed_agents), "overall_progress": task.progress}),
            user_id=user_id
        )
        db.add(audit)

        db.commit()
        db.refresh(delegation)
        db.refresh(task)
        return delegation

    @classmethod
    def execute_consequential_action(cls, delegation: models.Delegation, action_id: str, action_name: str, payload: dict, db: Session, user_id: int):
        """
        Level C Approval Gate: Explicit founder authorization for external/irreversible action
        (Posting to LinkedIn/Telegram, sending offer letters, spending budget).
        """
        task = delegation.task
        agent = delegation.agent

        action_result = {}

        if action_id == "publish_linkedin":
            action_result = MockSocialAdapter.publish_linkedin("Published via FounderOS Agent")
        elif action_id == "publish_telegram":
            action_result = MockSocialAdapter.publish_telegram("Broadcasted via FounderOS Agent")
        elif action_id in ["send_offer_letter", "approve_send_offer"]:
            cand_name = payload.get("candidate_name", "Candidate")
            doc_id = payload.get("document_id", "DOC-001")
            action_result = MockDocumentService.dispatch_docusign_envelope(doc_id, cand_name)
        else:
            action_result = {
                "action_id": action_id,
                "status": "EXECUTED",
                "executed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "authorized_by": "Founder"
            }

        # Append to actions_taken on the delegation
        actions_taken = json.loads(delegation.actions_taken or "[]")
        actions_taken.append({
            "action_id": action_id,
            "action_name": action_name,
            "result": action_result,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        })
        delegation.actions_taken = json.dumps(actions_taken)

        # Record Consequential Action Approval
        appr = models.Approval(
            title=f"Action Authorization: {action_name}",
            approval_level="CONSEQUENTIAL_ACTION_APPROVAL",
            action_name=action_name,
            decision="APPROVED",
            action_payload=json.dumps(action_result),
            task_id=task.id,
            delegation_id=delegation.id,
            user_id=user_id
        )
        db.add(appr)

        # Audit Log
        audit = models.AuditLog(
            task_id=task.id,
            agent_name=f"{agent} Agent",
            action_type="CONSEQUENTIAL_ACTION",
            summary=f"Founder explicitly authorized consequential action: '{action_name}'.",
            details=json.dumps(action_result),
            user_id=user_id
        )
        db.add(audit)

        db.commit()
        db.refresh(delegation)
        return {"status": "SUCCESS", "action_result": action_result, "delegation": delegation}