from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = FastAPI()

tasks_db = [
    {
        "id": 1,
        "title": "Thiet ke database Shop AI",
        "description": "Xay dung bang va toi uu index",
        "assignee": "QuyDev",
        "priority": 1,
        "status": "todo",
        "created_at": "2026-07-01T09:00:00Z"
    },
    {
        "id": 2,
        "title": "Code bo API Authen",
        "description": "Trien khai filter verify JWT token",
        "assignee": "FixerQ",
        "priority": 2,
        "status": "done",
        "created_at": "2026-07-01T10:00:00Z"
    }
]

ALLOWED_STATUS = ["todo", "in_progress", "done"]


class TaskCreateSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=1)
    assignee: str = Field(..., min_length=1)
    priority: int = Field(..., ge=1, le=5)


class TaskStatusUpdateSchema(BaseModel):
    status: str


def now():
    return datetime.utcnow().isoformat() + "Z"


def response(status, message, data, error, path):
    return JSONResponse(
        status_code=status,
        content={
            "statusCode": status,
            "message": message,
            "data": data,
            "error": error,
            "timestamp": now(),
            "path": path
        }
    )


@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    return response(
        exc.status_code,
        "Có lỗi xảy ra!",
        None,
        exc.detail,
        request.url.path
    )


@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    return response(
        422,
        "Lỗi dữ liệu đầu vào!",
        None,
        "ERR-422: Dữ liệu không hợp lệ.",
        request.url.path
    )
    
@app.get("/tasks")
def get_all_tasks(request: Request, status: Optional[str] = None):

    if status:
        data = []
        for task in tasks_db:
            if task["status"] == status:
                data.append(task)
    else:
        data = tasks_db

    return response(
        200,
        "Lấy danh sách công việc thành công!",
        data,
        None,
        request.url.path
    )


@app.post("/tasks")
def create_task(task_in: TaskCreateSchema, request: Request):

    for task in tasks_db:
        if task["title"].lower() == task_in.title.lower():
            raise HTTPException(
                status_code=400,
                detail="ERR-TASK-01: Task conflict: Title field duplicates an existing record."
            )

    if len(tasks_db) == 0:
        new_id = 1
    else:
        new_id = max(task["id"] for task in tasks_db) + 1

    new_task = {
        "id": new_id,
        "title": task_in.title,
        "description": task_in.description,
        "assignee": task_in.assignee,
        "priority": task_in.priority,
        "status": "todo",
        "created_at": now()
    }

    tasks_db.append(new_task)

    return response(
        201,
        "Khởi tạo công việc mới thành công!",
        new_task,
        None,
        request.url.path
    )
    
@app.put("/tasks/{task_id}")
def update_task_status(
    task_id: int,
    status_in: TaskStatusUpdateSchema,
    request: Request
):

    if status_in.status not in ALLOWED_STATUS:
        raise HTTPException(
            status_code=400,
            detail="ERR-TASK-02: Invalid task status."
        )

    for task in tasks_db:

        if task["id"] == task_id:

            if task["status"] == "done":
                raise HTTPException(
                    status_code=400,
                    detail="ERR-TASK-04: Completed task cannot be updated."
                )

            task["status"] = status_in.status

            return response(
                200,
                "Cập nhật tiến độ công việc thành công!",
                task,
                None,
                request.url.path
            )

    raise HTTPException(
        status_code=404,
        detail="ERR-TASK-03: Task not found."
    )


def calculate_team_metrics():

    total_tasks = len(tasks_db)

    completed_tasks = 0

    for task in tasks_db:
        if task["status"] == "done":
            completed_tasks += 1

    if total_tasks == 0:
        completion_rate = 0
    else:
        completion_rate = completed_tasks * 100 / total_tasks

    return total_tasks, completed_tasks, completion_rate


@app.get("/tasks/analytics/dashboard")
def get_dashboard_analytics(request: Request):

    total, completed, rate = calculate_team_metrics()

    data = {
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_rate_percentage": rate
    }

    return response(
        200,
        "Lấy số liệu thống kê hiệu suất nhóm thành công!",
        data,
        None,
        request.url.path
    )