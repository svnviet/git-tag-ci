from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from ..db import SessionLocal, Tag
from ..templating import templates
from .downloads import FINISHED

router = APIRouter(include_in_schema=False)

STATUSES = ["pending", "building", "success", "failed", "skipped", "invalid", "ignored"]


def _read(path: str | None, tail: int | None = None) -> str | None:
    if not path or not Path(path).is_file():
        return None
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-tail:] if tail else lines)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, status: str | None = None):
    with SessionLocal() as s:
        q = select(Tag).order_by(Tag.discovered_at.desc(), Tag.name.desc())
        if status:
            q = q.where(Tag.status == status)
        tags = list(s.scalars(q))
    return templates.TemplateResponse(
        request,
        "index.html",
        {"tags": tags, "statuses": STATUSES, "current": status, "finished": FINISHED},
    )


@router.get("/ui/tags/{name:path}", response_class=HTMLResponse)
def tag_page(request: Request, name: str):
    with SessionLocal() as s:
        t = s.get(Tag, name)
    if not t:
        raise HTTPException(404, "tag not found")
    return templates.TemplateResponse(
        request,
        "tag.html",
        {
            "t": t,
            "finished": t.status in FINISHED,
            "notes": _read(t.notes_path),
            "log_tail": _read(t.log_path, tail=200),
        },
    )
