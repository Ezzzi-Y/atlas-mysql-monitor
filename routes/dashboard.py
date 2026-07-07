# routes/dashboard.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def dashboard(request: Request):
    """仪表盘页面"""
    return templates.TemplateResponse(
        request,
        "dashboard.html",
    )
