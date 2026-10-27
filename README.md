# git-tag-ci

Polls the git tags of a repo; a new tag with a configured prefix is checked out
(`git checkout tags/<tag>`) and a build script (`.bat`) is run for it. Release notes are
generated from the commits between the previous tag with the same prefix and the new tag.

## Run (Windows, Git installed)
    pip install -r requirements.txt
    copy .env.example .env      # then edit REPO_URL / WORK_DIR / BUILD_SCRIPT / TAG_PREFIXES ...
    run.bat

## How a tag is handled
- Tag does not start with a configured prefix -> `ignored`.
- Params contain characters outside `A-Za-z0-9_.+=@` -> `invalid` (never passed to cmd).
- Otherwise -> `pending` -> `building` -> `success` / `failed` (exit code of the script).
- The script receives `BUILD_ARGS` (default `{params}`): `{tag}`, `{prefix}`, `{params}`, `{output}`, `{notes}`, `{prev}`, `{log}`.
- "Previous tag" (for the release note) = the tag with the same prefix that was synced just before it (`discovered_at`).
- Each tag gets `OUTPUT_DIR/<tag>/` containing `ReleaseNote.md`.

## Database and migrations
- SQLite by default (`DB_URL=sqlite:///./tags.db`). For PostgreSQL set either
  `DB_URL=postgresql+psycopg://user:password@host:5432/git_tag_ci` or the parts
  `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (leave `DB_URL` unset). The database must already exist.
- Schema is managed with Alembic. The service runs `alembic upgrade head` on startup, so nothing else is needed.
  Databases created before Alembic was added are upgraded in place.
- Manual use: `alembic upgrade head`, `alembic current`, `alembic revision --autogenerate -m "change"` (after editing `app/db.py`).

## API
- `GET  /tags[?status=pending|building|success|failed|skipped|ignored|invalid]`
- `GET  /tags/{name}` | `GET /tags/{name}/log` | `GET /tags/{name}/release-notes`
- `POST /tags/{name}/build` - build again
- `POST /sync` - fetch now instead of waiting for the next poll
- Swagger: http://localhost:8000/docs

Notes: on the first run, tags that already exist are marked `skipped` (set `BUILD_EXISTING=true` to build them all).
Private repos: use a URL with a token or configure a Git credential helper.

## Run as a Windows service (starts with Windows)
1. Download [NSSM](https://nssm.cc/download) and put `nssm.exe` in PATH or in the `service/` folder.
2. Configure `.env` (the service runs `run.bat`, which loads it).
3. Open cmd as **Administrator**:
       service\install_service.bat .\<user> <password>
   (use your own account so the service has your git credentials and Unity license; omit the arguments to run as LocalSystem)
4. Remove it with `service\uninstall_service.bat`. Service logs: `logs\service.out.log`, `logs\service.err.log`.
