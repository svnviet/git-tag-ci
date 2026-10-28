import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parent.parent
# Load <project>/.env regardless of the working directory; real environment variables take precedence
load_dotenv(ROOT / ".env")


def _bool(v: str) -> bool:
    return v.strip().lower() in ("1", "true", "yes", "on")


REPO_URL = os.environ.get("REPO_URL", "")
WORK_DIR = Path(os.environ.get("WORK_DIR", "./work/repo")).resolve()
BUILD_SCRIPT = os.environ.get("BUILD_SCRIPT", "build.bat")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))
BUILD_EXISTING = _bool(os.environ.get("BUILD_EXISTING", "false"))
GIT_BIN = os.environ.get("GIT_BIN", "git")


def _db_url() -> str:
    # 1) DB_URL wins; 2) otherwise build a PostgreSQL URL from DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD
    # (URL.create escapes special characters in the password); 3) fall back to local SQLite
    if os.environ.get("DB_URL"):
        return os.environ["DB_URL"]
    if os.environ.get("DB_HOST"):
        return URL.create(
            "postgresql+psycopg",
            username=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD") or None,
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "5432")),
            database=os.environ.get("DB_NAME", "git_tag_ci"),
        ).render_as_string(hide_password=False)
    return "sqlite:///./tags.db"


DB_URL = _db_url()
LOG_DIR = Path(os.environ.get("LOG_DIR", "./logs")).resolve()
BUILD_TIMEOUT = int(os.environ.get("BUILD_TIMEOUT", "3600"))

# Only tags starting with one of these prefixes are built (comma separated)
TAG_PREFIXES = [
    p.strip()
    for p in os.environ.get("TAG_PREFIXES", "release-").split(",")
    if p.strip()
]
# The part after the prefix is split by this separator into params passed to the script
TAG_PARAM_SEP = os.environ.get("TAG_PARAM_SEP", "-")

# Command used to run the build script. Windows: "cmd /c" (default); e.g. "bash" to test on Mac/Linux
BAT_RUNNER = os.environ.get("BAT_RUNNER", "cmd /c").split()

# Argument template passed to the script. Placeholders: {tag} full tag name, {prefix}, {params} (parts after the prefix split by TAG_PARAM_SEP),
# {output} per-tag output dir, {notes} release notes file, {prev} previous tag with the same prefix,
# {log} path for the build tool's own log (OUTPUT_DIR/<tag>/build.log)
BUILD_ARGS = os.environ.get("BUILD_ARGS", "{params}").split()

# Flags for git clean before building. Do NOT use -x: it would delete ignored dirs such as Unity Library/
GIT_CLEAN_ARGS = os.environ.get("GIT_CLEAN_ARGS", "-fd").split()

# Each tag gets its own output dir: OUTPUT_DIR/<tag>/ (also holds ReleaseNote.md)
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output")).resolve()
