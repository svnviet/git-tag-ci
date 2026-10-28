from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from .. import worker
from ..db import SessionLocal, Tag

router = APIRouter(tags=["tags"])


def _dict(t: Tag) -> dict:
    return {
        c.name: getattr(t, c.name)
        for c in Tag.__table__.columns
        if c.name not in ("log_path", "notes_path")
    }


@router.get("/tags")
def list_tags(status: str | None = None):
    with SessionLocal() as s:
        q = select(Tag).order_by(Tag.discovered_at.desc(), Tag.name.desc())
        if status:
            q = q.where(Tag.status == status)
        return [_dict(t) for t in s.scalars(q)]


@router.get("/tags/{name:path}/log", response_class=PlainTextResponse)
def tag_log(name: str):
    with SessionLocal() as s:
        t = s.get(Tag, name)
    if not t or not t.log_path or not Path(t.log_path).exists():
        raise HTTPException(404, "no log available")
    return Path(t.log_path).read_text(encoding="utf-8", errors="replace")


@router.get("/tags/{name:path}/release-notes", response_class=PlainTextResponse)
def release_notes(name: str):
    with SessionLocal() as s:
        t = s.get(Tag, name)
    if not t or not t.notes_path or not Path(t.notes_path).exists():
        raise HTTPException(404, "no release notes yet (tag has not been built)")
    return Path(t.notes_path).read_text(encoding="utf-8")


@router.post("/tags/{name:path}/build", status_code=202)
def rebuild(name: str):
    """Put the tag back to pending so it is built again."""
    with SessionLocal() as s:
        t = s.get(Tag, name)
        if not t:
            raise HTTPException(404, "tag not found")
        if t.status == "building":
            raise HTTPException(409, "already building")
        t.status = "pending"
        s.commit()
    worker.trigger()
    return {"queued": name}


@router.get("/tags/{name:path}")
def get_tag(name: str):
    with SessionLocal() as s:
        t = s.get(Tag, name)
    if not t:
        raise HTTPException(404, "tag not found")
    return _dict(t)


@router.post("/sync", status_code=202)
def sync_now():
    worker.trigger()
    return {"triggered": True}
