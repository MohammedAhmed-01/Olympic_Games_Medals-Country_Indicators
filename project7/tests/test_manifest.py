"""Tests for raw manifest integrity."""

import src.manifest as manifest


def test_register_verify_and_one_byte_change(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(manifest, "MANIFEST_PATH", tmp_path / "MANIFEST.csv")
    scratch = tmp_path / "scratch.csv"
    scratch.write_bytes(b"a,b\n1,2\n")
    row = manifest.register_file(scratch, "https://example.test/scratch", "2026-01-01T00:00:00Z", 1, "test")
    assert row["sha256"]
    manifest.verify_manifest()
    scratch.write_bytes(b"a,b\n1,3\n")
    try:
        manifest.verify_manifest()
    except ValueError as error:
        assert "scratch" in str(error) or "hash mismatch" in str(error)
    else:
        raise AssertionError("verify_manifest should fail after changing one byte")
