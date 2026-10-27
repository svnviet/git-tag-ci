import json
import logging
import os
import re
import subprocess
import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from . import config
from .db import SessionLocal, Tag, now

log = logging.getLogger("worker")
_lock = threading.Lock()  # one sync/build at a time (single shared working tree)
_wake = threading.Event()
_stop = threading.Event()


def _git(*args: str, check: bool = True) -> str:
    r = subprocess.run(
        [config.GIT_BIN, *args], cwd=config.WORK_DIR if config.WORK_DIR.exists() else None,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


_SAFE_PARAM = re.compile(r"^[A-Za-z0-9_._+=@]+$")  # avoid cmd special characters (& | ^ % ...)


def parse_tag(name: str) -> tuple[str, list[str]] | None:
    """Return (prefix, params) if the tag matches a prefix, else None."""
    for prefix in config.TAG_PREFIXES:
        if name.startswith(prefix):
            rest = name[len(prefix):]
            return prefix, [p for p in rest.split(config.TAG_PARAM_SEP) if p]
    return None


def _classify(name: str, first_run: bool) -> tuple[str, list[str]]:
    parsed = parse_tag(name)
    if not parsed:
        return "ignored", []
    params = parsed[1]
    if not all(_SAFE_PARAM.match(p) for p in params):
        return "invalid", params
    if first_run and not config.BUILD_EXISTING:
        return "skipped", params
    return "pending", params


def prev_tag(name: str) -> str | None:
    """Tag with the same prefix that was synced (discovered) just before `name`."""
    prefix = (parse_tag(name) or ("", []))[0]
    with SessionLocal() as s:
        rows = s.execute(select(Tag.name).order_by(Tag.discovered_at, Tag.name)).scalars().all()
    same = [t for t in rows if (parse_tag(t) or ("",))[0] == prefix]
    i = same.index(name) if name in same else -1
    return same[i - 1] if i > 0 else None


def write_release_notes(name: str, prev: str | None, out_dir) -> str:
    """Write ReleaseNote.md: `git log <prev>..<tag> --pretty=format:"- %s"` under a title line."""
    cmd = ["log", "--pretty=format:- %s", f"{prev}..{name}" if prev else name]
    if not prev:
        cmd.insert(1, "-n100")  # first tag of this prefix: limit to the latest 100 commits
    commits = _git(*cmd).strip() or "- (no new commits)"
    title = f"# Release Note - {prev} to {name}" if prev else f"# Release Note - {name}"
    path = out_dir / "ReleaseNote.md"
    path.write_text(f"{title}\n{commits}\n", encoding="utf-8")
    return str(path)


def _build_args(name: str, params: list[str], ctx: dict[str, str]) -> list[str]:
    prefix = (parse_tag(name) or ("", []))[0]
    out: list[str] = []
    for tok in config.BUILD_ARGS:
        if tok == "{params}":
            out.extend(params)
        else:
            tok = tok.replace("{tag}", name).replace("{prefix}", prefix)
            for k, v in ctx.items():
                tok = tok.replace("{" + k + "}", v)
            out.append(tok)
    return out


def _ensure_repo() -> None:
    if (config.WORK_DIR / ".git").exists():
        return
    if not config.REPO_URL:
        raise RuntimeError("REPO_URL is not configured")
    config.WORK_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([config.GIT_BIN, "clone", config.REPO_URL, str(config.WORK_DIR)], check=True)


def sync_tags() -> int:
    """Fetch tags from the remote and store new ones in the DB. Returns the number of new tags."""
    with _lock:
        _ensure_repo()
        _git("fetch", "--tags", "--force", "--prune", "origin")
        out = _git("for-each-ref", "--format=%(refname:short) %(*objectname) %(objectname) %(creatordate:unix)",
                   "--sort=creatordate", "refs/tags")
        found = []
        for line in out.splitlines():
            parts = line.split()
            # annotated tag: parts = name, commit, tag object, date; lightweight: name, commit, date.
            # date = tagger date (annotated) or commit date (lightweight)
            found.append((parts[0], parts[1], datetime.fromtimestamp(int(parts[-1]), timezone.utc)))

        with SessionLocal() as s:
            known = set(s.scalars(select(Tag.name)))
            first_run = not known
            new = [t for t in found if t[0] not in known]
            base = now()
            last = None
            for n, c, git_date in new:
                status, params = _classify(n, first_run)
                # First sync: the tags already exist, so use the git date as their time.
                # Later syncs: use the moment they were discovered. Either way keep a strict order
                # inside one batch (git order) with a 1 microsecond step.
                at = git_date if first_run else base
                if last is not None and at <= last:
                    at = last + timedelta(microseconds=1)
                last = at
                s.add(Tag(name=n, commit=c, status=status, params=json.dumps(params), discovered_at=at))
            s.commit()
        if new:
            log.info("new tags: %s", [t[0] for t in new])
        return len(new)


def build_tag(name: str) -> None:
    with _lock:
        with SessionLocal() as s:
            tag = s.get(Tag, name)
            tag.status, tag.started_at, tag.finished_at, tag.exit_code = "building", now(), None, None
            config.LOG_DIR.mkdir(parents=True, exist_ok=True)
            log_file = config.LOG_DIR / f"{name.replace('/', '_')}-{tag.started_at:%Y%m%d%H%M%S}.log"
            tag.log_path = str(log_file)
            s.commit()

            code = -1
            with open(log_file, "w", encoding="utf-8", errors="replace") as f:
                try:
                    _git("checkout", "-f", f"tags/{name}")
                    _git("clean", *config.GIT_CLEAN_ARGS, check=False)
                    script = config.WORK_DIR / config.BUILD_SCRIPT
                    prev = prev_tag(name)
                    out_dir = config.OUTPUT_DIR / name.replace("/", "_")
                    out_dir.mkdir(parents=True, exist_ok=True)
                    tag.prev_tag, tag.output_dir = prev, str(out_dir)
                    tag.notes_path = write_release_notes(name, prev, out_dir)
                    s.commit()
                    safe_prev = prev if prev and _SAFE_PARAM.match(prev) else ""
                    ctx = {"output": str(out_dir), "notes": tag.notes_path, "prev": safe_prev,
                           "log": str(out_dir / "build.log")}
                    params = _build_args(name, json.loads(tag.params or "[]"), ctx)
                    f.write(f"$ {script} {' '.join(params)}\n")
                    f.flush()
                    code = subprocess.run(
                        [*config.BAT_RUNNER, str(script), *params], cwd=config.WORK_DIR,
                        env={**os.environ, "TAG_NAME": name, "PREV_TAG": safe_prev,
                             "OUTPUT_DIR": str(out_dir), "RELEASE_NOTES": tag.notes_path,
                             "BUILD_LOG": str(out_dir / "build.log")},
                        stdout=f, stderr=subprocess.STDOUT, timeout=config.BUILD_TIMEOUT,
                    ).returncode
                except Exception as e:  # noqa: BLE001
                    f.write(f"\n[service error] {e!r}\n")

            tag.exit_code, tag.finished_at = code, now()
            tag.status = "success" if code == 0 else "failed"
            s.commit()
            log.info("build %s -> %s", name, tag.status)


def _cycle() -> None:
    try:
        sync_tags()
        while True:
            with SessionLocal() as s:
                nxt = s.scalars(
                    select(Tag.name).where(Tag.status == "pending").order_by(Tag.discovered_at, Tag.name).limit(1)
                ).first()
            if not nxt:
                break
            build_tag(nxt)
    except Exception:  # noqa: BLE001
        log.exception("cycle failed")


def _loop() -> None:
    while not _stop.is_set():
        _cycle()
        _wake.wait(config.POLL_INTERVAL)
        _wake.clear()


def start() -> threading.Thread:
    # reset builds left unfinished when the service was stopped abruptly
    with SessionLocal() as s:
        for t in s.scalars(select(Tag).where(Tag.status == "building")):
            t.status = "pending"
        s.commit()
    th = threading.Thread(target=_loop, name="tag-worker", daemon=True)
    th.start()
    return th


def stop() -> None:
    _stop.set()
    _wake.set()


def trigger() -> None:
    _wake.set()
