import subprocess
import sys
from pathlib import Path


def test_self_test_entrypoint() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, str(root / "run.py"), "--self-test"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "self-test passed" in result.stdout
