import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routes import (
    admin,
    auth,
    baselines,
    comments,
    health,
    notifications,
    requirements,
    test_cases,
    traceability,
    ui_module4,
    verification,
)
from src.shared.errors import AppError, app_error_handler
from src.shared.settings import settings


app = FastAPI(title=settings.app_name)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get(settings.request_id_header, str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[settings.request_id_header] = request_id
    return response


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return app_error_handler(request, exc)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(requirements.router)
app.include_router(baselines.router)
app.include_router(comments.router)
app.include_router(notifications.router)
app.include_router(traceability.router)
app.include_router(test_cases.router)
app.include_router(verification.router)
app.include_router(ui_module4.router)
