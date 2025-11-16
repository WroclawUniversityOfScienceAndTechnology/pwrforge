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

DOCKER_TEMPLATES_DIR = (
    ROOT / "pwrforge" / "file_generators" / "templates" / "docker"
)

PYPROJECT = ROOT / "pyproject.toml"
CI_REQUIREMENTS = ROOT / "ci" / "requirements.txt"
DOCKER_REQUIREMENTS_TEMPLATE = DOCKER_TEMPLATES_DIR / "requirements.txt.j2"


def run(cmd: list[str]) -> None:
    """Run a subprocess command and print it."""
    print(f"--> RUN: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def build_wheel_and_copy() -> None:
    """Build pwrforge wheel and copy it into docker templates."""
    os.environ["PWRFORGE_BUILD_RUNNING"] = "1"

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DOCKER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Build wheel
    run([sys.executable, "-m", "build", "--wheel"])

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
    """Generate requirements for CI and docker."""
    CI_REQUIREMENTS.parent.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            "-m",
            "piptools",
            "compile",
            "--all-extras",
            "--output-file",
            str(CI_REQUIREMENTS),
            str(PYPROJECT),
        ]
    )

    run(
        [
            sys.executable,
            "-m",
            "piptools",
            "compile",
            "--output-file",
            str(DOCKER_REQUIREMENTS_TEMPLATE),
            str(PYPROJECT),
        ]
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
