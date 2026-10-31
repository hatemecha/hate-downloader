import io
import stat
import tarfile
import zipfile
from pathlib import Path

import pytest

from app.core.dependency_manager import DependencyManager


class TestSafeExtract:
    def test_blocks_zip_slip(self, tmp_path: Path) -> None:
        manager = DependencyManager()
        manager._tools_dir = tmp_path

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.txt", "pwned")
        buf.seek(0)

        archive = tmp_path / "bad.zip"
        archive.write_bytes(buf.getvalue())

        with pytest.raises(ValueError, match="Unsafe zip path"):
            manager._extract_archive(archive)

        assert not (tmp_path.parent / "evil.txt").exists()

    def test_extracts_nested_safe_member(self, tmp_path: Path) -> None:
        manager = DependencyManager()
        manager._tools_dir = tmp_path

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("aria2-1.37.0/aria2c.exe", "binary-stub")
        buf.seek(0)

        archive = tmp_path / "good.zip"
        archive.write_bytes(buf.getvalue())
        manager._extract_archive(archive)

        extracted = tmp_path / "aria2-1.37.0" / "aria2c.exe"
        assert extracted.exists()
        assert extracted.read_text() == "binary-stub"

    def test_blocks_tar_symlink(self, tmp_path: Path) -> None:
        manager = DependencyManager()
        manager._tools_dir = tmp_path
        archive = tmp_path / "bad.tar.gz"

        with tarfile.open(archive, "w:gz") as tf:
            link = tarfile.TarInfo("ffmpeg")
            link.type = tarfile.SYMTYPE
            link.linkname = "../outside"
            tf.addfile(link)

        with pytest.raises(ValueError, match="link or special file"):
            manager._extract_archive(archive)

    def test_blocks_zip_symlink(self, tmp_path: Path) -> None:
        manager = DependencyManager()
        manager._tools_dir = tmp_path
        archive = tmp_path / "bad.zip"

        with zipfile.ZipFile(archive, "w") as zf:
            link = zipfile.ZipInfo("ffmpeg")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(link, "../outside")

        with pytest.raises(ValueError, match="Archive link blocked"):
            manager._extract_archive(archive)
