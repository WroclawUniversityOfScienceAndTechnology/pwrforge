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
    print("Skipping build.py execution inside python -m build (avoiding recursion).")
    sys.exit(0)

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"

DOCKER_TEMPLATES_DIR = ROOT / "pwrforge" / "templates" / ".devcontainer"

PYPROJECT = ROOT / "pyproject.toml"
CI_REQUIREMENTS = ROOT / "ci" / "requirements.txt"
DOCKER_REQUIREMENTS_TEMPLATE = DOCKER_TEMPLATES_DIR / "requirements.txt"


def run(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
) -> None:
    """Run a subprocess command and print it."""
    cmd_str = " ".join(cmd)
    print(f"--> RUN: {cmd_str}")
    subprocess.check_call(cmd, env=env, cwd=str(cwd) if cwd is not None else None)


def build_wheel_and_copy() -> None:
    """Build pwrforge wheel and copy it into docker templates."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DOCKER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare env only for the build subprocess to avoid recursion
    build_env = os.environ.copy()
    build_env["PWRFORGE_BUILD_RUNNING"] = "1"

    # 1) Build wheel (must run in project root so python -m build widzi pyproject.toml)
    run(
        [sys.executable, "-m", "build", "--wheel"],
        env=build_env,
        cwd=ROOT,
    )

    # 2) Locate newest wheel
    wheels = sorted(DIST_DIR.glob("pwrforge-*-py3-none-any.whl"))
    if not wheels:
        raise SystemExit("No pwrforge wheel found in dist/")
    wheel = wheels[-1]

    # 3) Remove old wheels from templates
    for old in DOCKER_TEMPLATES_DIR.glob("pwrforge-*-py3-none-any.whl"):
        print(f"Removing old wheel: {old}")
        old.unlink()

    # 4) Copy wheel
    dest = DOCKER_TEMPLATES_DIR / wheel.name
    print(f"Copying wheel to docker templates: {dest}")
    shutil.copy2(wheel, dest)


def generate_requirements() -> None:
    CI_REQUIREMENTS.parent.mkdir(parents=True, exist_ok=True)
    DOCKER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    safe_cwd = ROOT  # tu akurat nazwa pliku nie przeszkadza dla pip-compile

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



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build helper for pwrforge.")
    parser.add_argument("--wheel", action="store_true", help="Build wheel only.")
    parser.add_argument("--reqs", action="store_true", help="Generate requirements only.")
    parser.add_argument("-a", "--all", action="store_true", help="Build wheel + requirements.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not any([args.wheel, args.reqs, args.all]):
        args.all = True

    if args.all or args.wheel:
        build_wheel_and_copy()

    if args.all or args.reqs:
        generate_requirements()


if __name__ == "__main__":
    main()
