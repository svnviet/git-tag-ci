"""Download endpoints. Files are named after the tag and are available once a build has finished,
whether it succeeded or failed (a failed build is where you most need the log)."""

import os
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from ..db import SessionLocal, Tag

router = APIRouter(tags=["downloads"])

FINISHED = ("success", "failed")


def _finished_tag(name: str) -> Tag:
    with SessionLocal() as s:
        t = s.get(Tag, name)
    if not t:
        raise HTTPException(404, "tag not found")
    if t.status not in FINISHED:
        raise HTTPException(
            409, f"tag is {t.status}; nothing to download until a build has finished"
        )
    return t


def _file_name(tag: str, suffix: str) -> str:
    return tag.replace("/", "_") + suffix


def _file_response(
    path: str | None, tag: str, suffix: str, media_type: str, what: str
) -> FileResponse:
    if not path or not Path(path).is_file():
        raise HTTPException(404, f"{what} not found")
    return FileResponse(path, media_type=media_type, filename=_file_name(tag, suffix))


@router.get("/tags/{name:path}/download/output")
def download_output(name: str):
    """The whole output folder as <tag>.zip (contents are under a <tag>/ folder inside the archive)."""
    t = _finished_tag(name)
    out = Path(t.output_dir or "")
    if not t.output_dir or not out.is_dir():
        raise HTTPException(404, "output folder not found")
    fd, tmp = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    root = name.replace("/", "_")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, f"{root}/{f.relative_to(out).as_posix()}")
    return FileResponse(
        tmp,
        media_type="application/zip",
        filename=_file_name(name, ".zip"),
        background=BackgroundTask(os.unlink, tmp),
    )


@router.get("/tags/{name:path}/download/release-note")
def download_release_note(name: str):
    """ReleaseNote.md as <tag>.md"""
    t = _finished_tag(name)
    return _file_response(
        t.notes_path, name, ".md", "text/markdown; charset=utf-8", "release note"
    )


@router.get("/tags/{name:path}/download/log")
def download_log(name: str):
    """What the build script printed (service log) as <tag>.log"""
    t = _finished_tag(name)
    return _file_response(t.log_path, name, ".log", "text/plain; charset=utf-8", "log")


@router.get("/tags/{name:path}/download/build-log")
def download_build_log(name: str):
    """The build tool's own log (BUILD_LOG, e.g. Unity's -logFile) as <tag>-build.log"""
    t = _finished_tag(name)
    path = str(Path(t.output_dir) / "build.log") if t.output_dir else None
    return _file_response(
        path, name, "-build.log", "text/plain; charset=utf-8", "build log"
    )
