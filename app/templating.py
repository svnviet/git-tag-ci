from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _dt(v: datetime | None) -> str:
    return v.strftime("%Y-%m-%d %H:%M:%S") if v else "-"


def _duration(t) -> str:
    if not (t.started_at and t.finished_at):
        return "-"
    sec = int((t.finished_at - t.started_at).total_seconds())
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s" if m else f"{s}s"


templates.env.filters["dt"] = _dt
templates.env.filters["duration"] = _duration
