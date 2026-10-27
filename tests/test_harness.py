"""Exercise real harness files and corrupt isolated temporary copies."""

import hashlib
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.verify_harness import verify


class HarnessVerificationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="wubs-harness-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = Path(__file__).resolve().parents[1]
        for directory in (".agents", "docs"):
            shutil.copytree(source / directory, self.root / directory)
        for filename in ("AGENTS.md", ".gitattributes"):
            shutil.copyfile(source / filename, self.root / filename)

    def manifest(self):
        return json.loads((self.root / ".agents/upstream.json").read_text("utf-8"))

    def save_manifest(self, manifest):
        (self.root / ".agents/upstream.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def make_archive(self, changed_source=None):
        manifest = self.manifest()
        archive = self.root / "upstream.zip"
        prefix = "agent-skills-" + manifest["commit"] + "/"
        with zipfile.ZipFile(archive, "w") as bundle:
            for destination, record in manifest["files"].items():
                data = (self.root / destination).read_bytes()
                if record["source"] == changed_source:
                    data += b"\nchanged\n"
                bundle.writestr(prefix + record["source"], data)
        manifest["archive"]["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.save_manifest(manifest)
        return archive

    def test_valid_installation(self):
        self.assertEqual([], verify(self.root))

    def test_changed_upstream_bytes(self):
        path = self.root / ".agents/skills/incremental-implementation/SKILL.md"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertIn("hash mismatch", "\n".join(verify(self.root)))

    def test_missing_shared_reference(self):
        (self.root / ".agents/references/definition-of-done.md").unlink()
        self.assertIn("definition-of-done.md", "\n".join(verify(self.root)))

    def test_missing_skill(self):
        (self.root / ".agents/skills/test-driven-development/SKILL.md").unlink()
        self.assertIn("skills", "\n".join(verify(self.root)))

    def test_extra_router_skill(self):
        router = self.root / ".agents/skills/using-agent-skills"
        router.mkdir()
        (router / "SKILL.md").write_text("unexpected skill", encoding="utf-8")
        self.assertIn("skills", "\n".join(verify(self.root)))

    def test_broken_reference_even_with_updated_hashes(self):
        destination = ".agents/skills/security-and-hardening/SKILL.md"
        path = self.root / destination
        data = path.read_bytes().replace(
            b"references/hardening-patterns.md", b"references/missing.md"
        )
        path.write_bytes(data)
        manifest = self.manifest()
        record = manifest["files"][destination]
        record["sha256"] = hashlib.sha256(data).hexdigest()
        record["git_blob_sha1"] = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest()
        self.save_manifest(manifest)
        self.assertIn("reference", "\n".join(verify(self.root)))

    def test_manifest_path_cannot_escape_workspace(self):
        manifest = self.manifest()
        manifest["files"]["../outside.md"] = {
            "source": "../outside.md",
            "sha256": "",
            "git_blob_sha1": "",
        }
        self.save_manifest(manifest)
        self.assertIn("Unsafe path", "\n".join(verify(self.root)))

    def test_missing_architecture_document(self):
        (self.root / "docs/ARCHITECTURE.md").unlink()
        self.assertIn("ARCHITECTURE.md", "\n".join(verify(self.root)))

    def test_invalid_manifest(self):
        (self.root / ".agents/upstream.json").write_text("{", encoding="utf-8")
        self.assertIn("manifest", "\n".join(verify(self.root)))

    def test_wrong_archive_digest(self):
        archive = self.root / "wrong.zip"
        archive.write_bytes(b"untrusted archive")
        self.assertIn("archive hash mismatch", "\n".join(verify(self.root, archive)))

    def test_valid_archive_comparison(self):
        self.assertEqual([], verify(self.root, self.make_archive()))

    def test_archive_content_mismatch(self):
        archive = self.make_archive("LICENSE")
        self.assertIn("archive content mismatch", "\n".join(verify(self.root, archive)))


if __name__ == "__main__":
    unittest.main()
