from __future__ import annotations

import hashlib
import importlib.util
import tarfile
from pathlib import Path

import kaggle_environments
from kaggle_environments import make

from scripts.package_submission import package


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission" / "main.py"
PUBLIC_C27 = ROOT / "opponents" / "public" / "c27" / "main.py"
PUBLIC_C27_SHA256 = "b7f17796744b0d7050618fc019b5647f2bad891eef8559e227efdea5c2338196"


def load_agent(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.agent)
    return module.agent


def test_engine_is_exact_version() -> None:
    assert kaggle_environments.__version__ == "1.32.2"


def test_control_hash_is_preserved() -> None:
    assert hashlib.sha256(PUBLIC_C27.read_bytes()).hexdigest() == PUBLIC_C27_SHA256


def test_self_play_finishes() -> None:
    left = load_agent(SUBMISSION, "control_left")
    right = load_agent(SUBMISSION, "control_right")
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": 0},
        debug=False,
    )
    env.run([left, right])
    assert [state.status for state in env.steps[-1]] == ["DONE", "DONE"]


def test_raw_file_loader_self_play_finishes() -> None:
    """Exercise Kaggle's get-last-callable path, not normal module import."""
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": 0},
        debug=False,
    )
    env.run([str(SUBMISSION), str(SUBMISSION)])
    assert [state.status for state in env.steps[-1]] == ["DONE", "DONE"]


def test_archive_contains_only_identical_main(tmp_path: Path) -> None:
    archive_path = tmp_path / "submission.tar.gz"
    digest = package(SUBMISSION, archive_path)
    assert digest == hashlib.sha256(SUBMISSION.read_bytes()).hexdigest()
    with tarfile.open(archive_path, "r:gz") as archive:
        assert archive.getnames() == ["main.py"]
        extracted = archive.extractfile("main.py")
        assert extracted is not None
        assert extracted.read() == SUBMISSION.read_bytes()
