from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SocialLogin(BaseModel):
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None


# CEO Planning Schemas
class CEOPlanStep(BaseModel):
    order: int
    agent: str
    responsibility: str
    dependencies: List[str] = []
    required_inputs: List[str] = []
    expected_output: str
    approval_required: bool = True

class CEOPlan(BaseModel):
    goal: str
    analysis: List[str] = []
    required_agents: List[str] = []
    skipped_agents: List[str] = []
    execution_steps: List[CEOPlanStep] = []
    risks: List[str] = []
    budget_estimate: Optional[str] = None
    recommended_order: List[str] = []

class PlanApprovalRequest(BaseModel):
    decision: str = "APPROVED"  # APPROVED, REJECTED, MODIFIED
    feedback: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None

class ConsequentialActionRequest(BaseModel):
    action_id: str
    action_name: str
    payload: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class RevisionRequest(BaseModel):
    feedback: str


class DelegationBase(BaseModel):
    agent: str
    task_description: str
    status: str = "BLOCKED"
    order_index: int = 1
    dependencies: Optional[str] = "[]"
    context_input: Optional[str] = "{}"
    decision_summary: Optional[str] = None
    result_output: Optional[str] = "{}"
    actions_available: Optional[str] = "[]"
    actions_taken: Optional[str] = "[]"
    error_message: Optional[str] = None

class DelegationCreate(DelegationBase):
    pass

class Delegation(DelegationBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    status: str = "DRAFT"
    date: str
    progress: int = 0
    summary: Optional[str] = None
    plan_data: Optional[str] = None
    goal_id: Optional[int] = None

class TaskCreate(BaseModel):
    title: str
    date: Optional[str] = None
    goal_id: Optional[int] = None

class Task(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    delegations: List[Delegation] = []

    class Config:
        from_attributes = True


class GoalBase(BaseModel):
    title: str
    risk: str = "Low"
    progress: int = 0
    completed_tasks: int = 0
    total_tasks: int = 0
    target_date: str

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    user_id: int
    created_at: datetime
    tasks: List[Task] = []

    class Config:
        from_attributes = True


class AgentActivityBase(BaseModel):
    agent_name: str
    action: str
    time: str
    icon_type: str
    bg_color: str

class AgentActivityCreate(AgentActivityBase):
    pass

class AgentActivity(AgentActivityBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentBase(BaseModel):
    name: str
    role: str

class AgentCreate(AgentBase):
    pass

class Agent(AgentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalBase(BaseModel):
    title: str
    approval_level: str = "PLAN_APPROVAL"
    action_name: Optional[str] = None
    decision: str = "APPROVED"
    feedback: Optional[str] = None
    action_payload: Optional[str] = None

class ApprovalCreate(ApprovalBase):
    task_id: Optional[int] = None
    delegation_id: Optional[int] = None

class Approval(ApprovalBase):
    id: int
    task_id: Optional[int] = None
    delegation_id: Optional[int] = None
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogBase(BaseModel):
    task_id: Optional[int] = None
    agent_name: str
    action_type: str
    summary: str
    details: Optional[str] = "{}"

class AuditLog(AuditLogBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentMessageBase(BaseModel):
    task_id: int
    sender: str
    recipient: str
    message_type: str
    content: str

class AgentMessage(AgentMessageBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowBase(BaseModel):
    name: str
    description: str

class WorkflowCreate(WorkflowBase):
    pass

class Workflow(WorkflowBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------
# Hiring Agent Schemas
# -----------------------------------------------------------------
class JobCreate(BaseModel):
    title: str
    department: Optional[str] = "Engineering"
    seniority: Optional[str] = "Mid-Level"
    target_compensation: Optional[str] = None
    required_skills: Optional[List[str]] = []
    experience_years: Optional[int] = 2

class CandidateCreate(BaseModel):
    name: str
    email: str
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: Optional[int] = 0

class MCQAnswerItem(BaseModel):
    question_id: int
    selected_option_index: int

class MCQSubmitRequest(BaseModel):
    answers: List[MCQAnswerItem]

class CodingRunRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    custom_input: Optional[str] = None

class CodingSubmitRequest(BaseModel):
    code: str
    language: Optional[str] = "python"

class FounderDecisionRequest(BaseModel):
    decision: str  # APPROVED, REJECTED, REVIEW_AGAIN
    notes: Optional[str] = None


