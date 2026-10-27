import os
from pathlib import Path


def _bool(v: str) -> bool:
    return v.strip().lower() in ("1", "true", "yes", "on")


REPO_URL = os.environ.get("REPO_URL", "")
WORK_DIR = Path(os.environ.get("WORK_DIR", "./work/repo")).resolve()
BUILD_SCRIPT = os.environ.get("BUILD_SCRIPT", "build.bat")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))
BUILD_EXISTING = _bool(os.environ.get("BUILD_EXISTING", "false"))
GIT_BIN = os.environ.get("GIT_BIN", "git")
DB_URL = os.environ.get("DB_URL", "sqlite:///./tags.db")
LOG_DIR = Path(os.environ.get("LOG_DIR", "./logs")).resolve()
BUILD_TIMEOUT = int(os.environ.get("BUILD_TIMEOUT", "3600"))

# Only tags starting with one of these prefixes are built (comma separated)
TAG_PREFIXES = [p.strip() for p in os.environ.get("TAG_PREFIXES", "release-").split(",") if p.strip()]
# The part after the prefix is split by this separator into params passed to the script
TAG_PARAM_SEP = os.environ.get("TAG_PARAM_SEP", "-")

# Command used to run the build script. Windows: "cmd /c" (default); e.g. "bash" to test on Mac/Linux
BAT_RUNNER = os.environ.get("BAT_RUNNER", "cmd /c").split()

# Argument template passed to the script. Placeholders: {tag} full tag name, {prefix}, {params} (parts after the prefix split by TAG_PARAM_SEP),
# {output} per-tag output dir, {notes} release notes file, {prev} previous tag with the same prefix
BUILD_ARGS = os.environ.get("BUILD_ARGS", "{params}").split()

# Flags for git clean before building. Do NOT use -x: it would delete ignored dirs such as Unity Library/
GIT_CLEAN_ARGS = os.environ.get("GIT_CLEAN_ARGS", "-fd").split()

# Each tag gets its own output dir: OUTPUT_DIR/<tag>/ (also holds release_notes.md)
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output")).resolve()
