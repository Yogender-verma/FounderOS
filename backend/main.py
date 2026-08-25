from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import timedelta
import os

import models
import schemas
from database import engine, get_db
import auth

# Create all tables (in a real app you'd use Alembic)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FounderOS API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        picture=user.picture
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/social", response_model=schemas.Token)
def social_login(social_user: schemas.SocialLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == social_user.email).first()
    if not user:
        import secrets
        random_password = auth.get_password_hash(secrets.token_urlsafe(32))
        new_user = models.User(
            email=social_user.email,
            hashed_password=random_password,
            full_name=social_user.full_name,
            picture=social_user.picture
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.User)
def read_users_me(current_user: Any = Depends(auth.get_current_user)):
    return current_user

import json
from datetime import datetime
from orchestrator import CEOOrchestrator

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    goals = db.query(models.Goal).filter(models.Goal.user_id == current_user.id).all()
    tasks = db.query(models.Task).filter(models.Task.user_id == current_user.id).order_by(models.Task.created_at.desc()).all()
    activities = db.query(models.AgentActivity).filter(models.AgentActivity.user_id == current_user.id).order_by(models.AgentActivity.created_at.desc()).limit(15).all()
    audit_logs = db.query(models.AuditLog).filter(models.AuditLog.user_id == current_user.id).order_by(models.AuditLog.created_at.desc()).limit(20).all()
    approvals = db.query(models.Approval).filter(models.Approval.user_id == current_user.id).order_by(models.Approval.created_at.desc()).limit(10).all()
    
    return {
        "goals": [schemas.Goal.model_validate(g) for g in goals],
        "tasks": [schemas.Task.model_validate(t) for t in tasks],
        "activities": [schemas.AgentActivity.model_validate(a) for a in activities],
        "audit_logs": [schemas.AuditLog.model_validate(al) for al in audit_logs],
        "approvals": [schemas.Approval.model_validate(ap) for ap in approvals]
    }

@app.get("/api/goals", response_model=List[schemas.Goal])
def read_goals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    goals = db.query(models.Goal).filter(models.Goal.user_id == current_user.id).offset(skip).limit(limit).all()
    return goals

@app.post("/api/goals", response_model=schemas.Goal)
def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    db_goal = models.Goal(**goal.model_dump(), user_id=current_user.id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@app.get("/api/tasks", response_model=List[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    tasks = db.query(models.Task).filter(models.Task.user_id == current_user.id).order_by(models.Task.created_at.desc()).offset(skip).limit(limit).all()
    return tasks

@app.post("/api/tasks", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    """
    Founder enters task -> Persistent Task created in DRAFT status.
    Task will be decomposed & assigned to agents ONLY when user clicks 'Delegate to CEO'.
    """
    date_str = task.date or datetime.now().strftime("%b %d, %Y")
    db_task = models.Task(
        title=task.title,
        date=date_str,
        goal_id=task.goal_id,
        status="DRAFT",
        progress=0,
        user_id=current_user.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/api/tasks/{task_id}", response_model=schemas.Task)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/tasks/{task_id}/plan/approve", response_model=schemas.Task)
def approve_plan(task_id: int, req: schemas.PlanApprovalRequest, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    """
    Level A Approval: Founder approves the CEO's overall execution plan.
    Transitions task to APPROVED and unlocks initial agent tasks to READY.
    """
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated_task = CEOOrchestrator.approve_plan(task, db, current_user.id, decision=req.decision, feedback=req.feedback)
    return updated_task

@app.post("/api/tasks/{task_id}/plan/reject", response_model=schemas.Task)
def reject_plan(task_id: int, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "REJECTED"
    db.commit()
    db.refresh(task)
    return task

@app.post("/api/tasks/{task_id}/analyze", response_model=schemas.Task)
@app.post("/api/tasks/{task_id}/delegate", response_model=schemas.Task)
def analyze_task(task_id: int, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    """
    Explicit 'Delegate to CEO' action:
    Takes a DRAFT task and triggers the CEO Agent to analyze, decompose into steps, and assign to specialized agents.
    """
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "CEO_ANALYZING"
    db.commit()

    updated_task = CEOOrchestrator.setup_task_workflow(task, db, current_user.id)
    return updated_task

@app.post("/api/agent-tasks/{delegation_id}/start", response_model=schemas.Delegation)
def start_agent_task(delegation_id: int, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    """
    Founder clicks START TASK inside the agent workspace.
    Executes the agent, gathers upstream context via CEO state, and produces structured results.
    """
    delegation = db.query(models.Delegation).filter(models.Delegation.id == delegation_id, models.Delegation.user_id == current_user.id).first()
    if not delegation:
        raise HTTPException(status_code=404, detail="Agent task not found")
    
    if delegation.status == "BLOCKED":
        raise HTTPException(status_code=400, detail="Task is blocked by upstream dependencies.")
    
    updated_del = CEOOrchestrator.execute_agent_task(delegation, db, current_user.id)
    return updated_del

@app.post("/api/agent-tasks/{delegation_id}/approve", response_model=schemas.Delegation)
def approve_agent_result(delegation_id: int, req: Optional[schemas.PlanApprovalRequest] = None, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    """
    Level B Approval: Founder reviews and approves the agent's generated result.
    Marks task COMPLETED, unblocks downstream dependencies, and updates project progress.
    """
    delegation = db.query(models.Delegation).filter(models.Delegation.id == delegation_id, models.Delegation.user_id == current_user.id).first()
    if not delegation:
        raise HTTPException(status_code=404, detail="Agent task not found")
    
    feedback = req.feedback if req else None
    updated_del = CEOOrchestrator.approve_agent_result(delegation, db, current_user.id, feedback=feedback)
    return updated_del

@app.post("/api/agent-tasks/{delegation_id}/consequential-action")
def execute_consequential_action(delegation_id: int, req: schemas.ConsequentialActionRequest, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    """
    Level C Approval Gate: Explicit founder authorization for external/consequential action
    (e.g., publishing to LinkedIn/Telegram, issuing offer letter).
    """
    delegation = db.query(models.Delegation).filter(models.Delegation.id == delegation_id, models.Delegation.user_id == current_user.id).first()
    if not delegation:
        raise HTTPException(status_code=404, detail="Agent task not found")
    
    res = CEOOrchestrator.execute_consequential_action(
        delegation=delegation,
        action_id=req.action_id,
        action_name=req.action_name,
        payload=req.payload or {},
        db=db,
        user_id=current_user.id
    )
    return {
        "status": "SUCCESS",
        "action_id": req.action_id,
        "action_result": res["action_result"],
        "delegation": schemas.Delegation.model_validate(res["delegation"])
    }

@app.post("/api/agent-tasks/{delegation_id}/revise", response_model=schemas.Delegation)
def revise_agent_task(delegation_id: int, req: schemas.RevisionRequest, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    """
    Requests revision on an agent result with specific founder feedback.
    """
    delegation = db.query(models.Delegation).filter(models.Delegation.id == delegation_id, models.Delegation.user_id == current_user.id).first()
    if not delegation:
        raise HTTPException(status_code=404, detail="Agent task not found")
    
    delegation.status = "NEEDS_REVISION"
    delegation.error_message = req.feedback
    
    audit = models.AuditLog(
        task_id=delegation.task_id,
        agent_name=f"{delegation.agent} Agent",
        action_type="REVISION",
        summary=f"Founder requested revision for {delegation.agent} Agent: '{req.feedback[:60]}'.",
        details=json.dumps({"feedback": req.feedback}),
        user_id=current_user.id
    )
    db.add(audit)
    db.commit()
    db.refresh(delegation)
    return delegation

@app.get("/api/audit-logs", response_model=List[schemas.AuditLog])
def get_audit_logs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: Any = Depends(auth.get_current_user)):
    logs = db.query(models.AuditLog).filter(models.AuditLog.user_id == current_user.id).order_by(models.AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs


# Include Autonomous 5-Agent Architecture Router
from agent_routes import router as agent_router
app.include_router(agent_router)

# Include Hiring Agent & Assessment Engine Router
from hiring_routes import router as hiring_router
app.include_router(hiring_router)

# -----------------------------------------------------------------
# Mount Unified Frontend Single-Page Application (SPA)
# -----------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

def get_frontend_dist():
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")),
        "E:\\frontend\\dist",
        os.path.abspath("../frontend/dist"),
        os.path.abspath("./frontend/dist"),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.exists(os.path.join(c, "index.html")):
            return c
    return None

dist_folder = get_frontend_dist()

if dist_folder and os.path.exists(dist_folder):
    assets_folder = os.path.join(dist_folder, "assets")
    if os.path.exists(assets_folder):
        app.mount("/assets", StaticFiles(directory=assets_folder), name="assets")

@app.get("/")
async def serve_root():
    """
    Explicit Root Handler: Serves the built frontend index.html at http://localhost:8000/
    """
    dist = get_frontend_dist()
    if dist:
        index_file = os.path.join(dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file, media_type="text/html")
    return HTMLResponse("<h2>FounderOS Backend is Online</h2><p>Frontend static build not found.</p>")

@app.get("/{full_path:path}")
async def serve_spa_and_assets(full_path: str):
    """
    SPA Catch-All Handler: Serves static assets or index.html for client-side routing.
    """
    # Allow API endpoints and Swagger documentation to bypass SPA catch-all
    if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path == "openapi.json":
        raise HTTPException(status_code=404, detail="Endpoint not found")

    dist = get_frontend_dist()
    if dist:
        # Check if requesting a direct static file (e.g. favicon.svg, icons.svg)
        if full_path:
            specific_file = os.path.join(dist, full_path)
            if os.path.isfile(specific_file):
                return FileResponse(specific_file)

        # Serve index.html for all SPA routes (/dashboard, /tasks, /agents, etc.)
        index_file = os.path.join(dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file, media_type="text/html")

    return HTMLResponse("<h2>FounderOS Backend is Online</h2><p>Frontend dist directory not found.</p>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
