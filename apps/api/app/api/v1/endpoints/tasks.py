from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.tenant_scoped import Task
from app.schemas.tasks import TaskCreate, TaskOut, TaskUpdate
from app.services import audit_service, notification_service

router = APIRouter()


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    status: str | None = Query(default=None),
    assignee_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    _: CurrentUser = Depends(require_permission("tasks.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[Task]:
    stmt = select(Task)
    if status:
        stmt = stmt.where(Task.status == status)
    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if department_id:
        stmt = stmt.where(Task.department_id == department_id)
    rows = (await db.execute(stmt.order_by(Task.created_at.desc()))).scalars()
    return list(rows)


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(
    payload: TaskCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("tasks.create")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Task:
    task = Task(**payload.model_dump(), created_by=current.id)
    db.add(task)
    await db.flush()
    await audit_service.record(
        db,
        user_id=current.id,
        action="tasks.create",
        resource_type="task",
        resource_id=str(task.id),
        metadata={"title": task.title, "priority": task.priority},
        request=request,
    )
    if task.assignee_id is not None and task.assignee_id != current.id:
        await notification_service.create_and_push(
            db,
            tenant_schema=current.tenant.schema_name,
            user_id=task.assignee_id,
            title=f"Yangi vazifa: {task.title}",
            body=task.description,
            category="tasks",
            severity="info",
            payload={"task_id": str(task.id), "priority": task.priority},
        )
    await db.commit()
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("tasks.update")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    fields = payload.model_dump(exclude_none=True)
    if "status" in fields and fields["status"] == "done" and task.completed_at is None:
        task.completed_at = datetime.now(UTC)
    for f, v in fields.items():
        setattr(task, f, v)

    await db.flush()
    await audit_service.record(
        db,
        user_id=current.id,
        action="tasks.update",
        resource_type="task",
        resource_id=str(task.id),
        metadata=fields,
        request=request,
    )
    await db.commit()
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("tasks.delete")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, str]:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await audit_service.record(
        db,
        user_id=current.id,
        action="tasks.delete",
        resource_type="task",
        resource_id=str(task_id),
        request=request,
    )
    await db.commit()
    return {"status": "deleted"}
