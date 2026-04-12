import os
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

import build_release


def test_build_wheel_and_copy_uses_newest_wheel_by_mtime(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    dist_dir = tmp_path / "dist"
    templates_dir = tmp_path / "templates"
    dist_dir.mkdir()
    templates_dir.mkdir()

    older_wheel = dist_dir / "pwrforge-0.0.9-py3-none-any.whl"
    newer_wheel = dist_dir / "pwrforge-0.0.10-py3-none-any.whl"
    older_wheel.write_text("old", encoding="utf-8")
    newer_wheel.write_text("new", encoding="utf-8")

    old_template_wheel = templates_dir / "pwrforge-0.0.9-py3-none-any.whl"
    old_template_wheel.write_text("stale", encoding="utf-8")

    monkeypatch.setattr(build_release, "DIST_DIR", dist_dir)
    monkeypatch.setattr(build_release, "DOCKER_TEMPLATES_DIR", templates_dir)
    monkeypatch.setattr(build_release, "run", lambda *args, **kwargs: None)

    os.utime(older_wheel, (1, 1))
    os.utime(newer_wheel, (2, 2))

    build_release.build_wheel_and_copy()

    assert not old_template_wheel.exists()
    copied_wheel = templates_dir / newer_wheel.name
    assert copied_wheel.exists()
    assert copied_wheel.read_text(encoding="utf-8") == "new"
    assert older_wheel.stat().st_mtime_ns <= newer_wheel.stat().st_mtime_ns
