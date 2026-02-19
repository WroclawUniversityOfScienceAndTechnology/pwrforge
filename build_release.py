#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Prevent recursive execution when python -m build runs inside a temp build env
if os.environ.get("PWRFORGE_BUILD_RUNNING") == "1":
    print("Skipping build_release.py execution inside python -m build (avoiding recursion).")
    sys.exit(0)

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"

DOCKER_TEMPLATES_DIR = ROOT / "pwrforge" / "templates" / ".devcontainer"

PYPROJECT = ROOT / "pyproject.toml"
CI_REQUIREMENTS = ROOT / "ci" / "requirements.txt"
DOCKER_REQUIREMENTS_TEMPLATE = DOCKER_TEMPLATES_DIR / "requirements.txt"

ENV_FILE = ROOT / ".env"


def run(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
) -> None:
    """Run a subprocess command and print it."""
    cmd_str = " ".join(cmd)
    print(f"--> RUN: {cmd_str}")
    subprocess.check_call(cmd, env=env, cwd=str(cwd) if cwd is not None else None)


def load_dotenv(dotenv_path: Path) -> dict[str, str]:
    """
    Load KEY=VALUE pairs from a .env file.
    - Supports comments (# ...)
    - Supports quoted values "..." or '...'
    - Does NOT do variable expansion
    """
    if not dotenv_path.exists():
        return {}

    data: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Strip surrounding quotes
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        if key:
            data[key] = value
    return data


def merge_env(base: dict[str, str], extra: dict[str, str]) -> dict[str, str]:
    """
    Merge env dicts such that values from `extra` override `base`.
    """
    merged = dict(base)
    merged.update(extra)
    return merged


def build_wheel_and_copy() -> None:
    """Build pwrforge wheel (and sdist for release) and copy wheel into docker templates."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DOCKER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare env only for the build subprocess to avoid recursion
    build_env = os.environ.copy()
    build_env["PWRFORGE_BUILD_RUNNING"] = "1"

    # Build wheel + sdist (recommended for PyPI)
    run(
        [sys.executable, "-m", "build", "--wheel", "--sdist"],
        env=build_env,
        cwd=ROOT,
    )

    # Locate newest wheel
    wheels = sorted(DIST_DIR.glob("pwrforge-*-py3-none-any.whl"))
    if not wheels:
        raise SystemExit("No pwrforge wheel found in dist/")
    wheel = wheels[-1]

    # Remove old wheels from templates
    for old in DOCKER_TEMPLATES_DIR.glob("pwrforge-*-py3-none-any.whl"):
        print(f"Removing old wheel: {old}")
        old.unlink()

    # Copy wheel
    dest = DOCKER_TEMPLATES_DIR / wheel.name
    print(f"Copying wheel to docker templates: {dest}")
    shutil.copy2(wheel, dest)


def generate_requirements() -> None:
    CI_REQUIREMENTS.parent.mkdir(parents=True, exist_ok=True)
    DOCKER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    safe_cwd = ROOT  # filename doesn't matter for pip-compile

    run(
        [
            "rm",
            "-f",
            str(CI_REQUIREMENTS),
        ],
        cwd=safe_cwd,
    )

    run(
        [
            "pip-compile",
            "--all-extras",
            "--output-file",
            str(CI_REQUIREMENTS),
            str(PYPROJECT),
        ],
        cwd=safe_cwd,
    )

    run(
        [
            "pip-compile",
            "--output-file",
            str(DOCKER_REQUIREMENTS_TEMPLATE),
            str(PYPROJECT),
        ],
        cwd=safe_cwd,
    )


def publish(repository: str, skip_existing: bool = True) -> None:
    """
    Upload dist/* to PyPI or TestPyPI using twine.
    Credentials are taken from env (.env merged with current environment):
      - TWINE_USERNAME (usually __token__)
      - TWINE_PASSWORD (pypi-.... token)
    """
    if not DIST_DIR.exists():
        raise SystemExit("dist/ does not exist. Run build first.")

    files = sorted(DIST_DIR.glob("*"))
    if not files:
        raise SystemExit("dist/ is empty. Nothing to upload.")

    dotenv = load_dotenv(ENV_FILE)
    publish_env = merge_env(os.environ.copy(), dotenv)

    # Basic sanity checks for credentials
    if not publish_env.get("TWINE_USERNAME") or not publish_env.get("TWINE_PASSWORD"):
        raise SystemExit("Missing TWINE_USERNAME or TWINE_PASSWORD.\nPut them into .env or export them in your shell.")

    # Validate metadata / long_description, etc.
    run([sys.executable, "-m", "twine", "check", "dist/*"], cwd=ROOT)

    cmd = [sys.executable, "-m", "twine", "upload"]
    if skip_existing:
        cmd.append("--skip-existing")
    cmd += ["--repository", repository, "dist/*"]

    run(cmd, cwd=ROOT, env=publish_env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/release helper for pwrforge.")
    parser.add_argument("--wheel", action="store_true", help="Build wheel (+ sdist) and copy wheel to templates.")
    parser.add_argument("--reqs", action="store_true", help="Generate requirements only.")
    parser.add_argument("-a", "--all", action="store_true", help="Build wheel(+sdist) + requirements.")
    parser.add_argument(
        "--publish",
        choices=["pypi", "testpypi"],
        help="Upload dist/* via twine (reads creds from .env or env vars).",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="When publishing: skip files that already exist on the repository.",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="When publishing: do NOT skip existing (twine will fail if version exists).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not any([args.wheel, args.reqs, args.all, args.publish]):
        # Default behavior: build everything (no publish)
        args.all = True

    if args.all or args.wheel:
        build_wheel_and_copy()

    if args.all or args.reqs:
        generate_requirements()

    if args.publish:
        # Resolve skip_existing default: True, unless user explicitly disables
        if args.no_skip_existing:
            skip_existing = False
        elif args.skip_existing:
            skip_existing = True
        else:
            skip_existing = True

        publish(args.publish, skip_existing=skip_existing)


if __name__ == "__main__":
    main()
