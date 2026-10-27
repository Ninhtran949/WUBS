"""Verify the repository-local engineering harness without network access."""

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

SKILLS = {
    "spec-driven-development",
    "planning-and-task-breakdown",
    "incremental-implementation",
    "test-driven-development",
    "code-review-and-quality",
    "security-and-hardening",
}
REQUIRED = (
    "AGENTS.md",
    ".gitattributes",
    ".agents/LICENSE",
    "docs/PROJECT.md",
    "docs/ARCHITECTURE.md",
    "docs/adr/README.md",
    "docs/plans/README.md",
)
REFERENCES = re.compile(r"(?<![\w/])(?:\.\./)*references/[\w./-]+\.md")


def verify(root, archive=None):
    root = Path(root).resolve()
    errors = [
        "Missing required file: " + name
        for name in REQUIRED
        if not (root / name).is_file()
    ]
    try:
        manifest = json.loads((root / ".agents/upstream.json").read_text("utf-8"))
        files = manifest["files"]
        commit = manifest["commit"]
        if not isinstance(files, dict) or not files:
            raise ValueError("files must be a nonempty mapping")
        if (
            manifest["repository"] != "https://github.com/addyosmani/agent-skills"
            or not re.fullmatch(r"[0-9a-f]{40}", commit)
            or manifest["archive"]["url"]
            != "https://codeload.github.com/addyosmani/agent-skills/zip/" + commit
        ):
            raise ValueError("source must identify a pinned upstream commit")
        if not re.fullmatch(r"[0-9a-f]{64}", manifest["archive"]["sha256"]):
            raise ValueError("archive must have a SHA-256 digest")
    except (OSError, ValueError, KeyError, TypeError) as error:
        return errors + ["Invalid upstream manifest: " + str(error)]

    actual_skills = (
        {p.name for p in (root / ".agents/skills").iterdir() if p.is_dir()}
        if (root / ".agents/skills").is_dir()
        else set()
    )
    if actual_skills != SKILLS:
        errors.append("Installed skills must be exactly the six approved skills")
    expected_manifests = {".agents/skills/" + name + "/SKILL.md" for name in SKILLS}
    if not expected_manifests.issubset(files):
        errors.append("Upstream manifest is missing required skills")
    inventory = {
        p.relative_to(root).as_posix()
        for directory in (".agents/skills", ".agents/references")
        for p in (root / directory).rglob("*")
        if p.is_file()
    }
    if (root / ".agents/LICENSE").is_file():
        inventory.add(".agents/LICENSE")
    if inventory != set(files):
        errors.append("Vendored file inventory differs from upstream manifest")

    contents = {}
    for destination, record in files.items():
        relative = PurePosixPath(destination)
        target = root / relative
        if (
            not destination.startswith(".agents/")
            or "\\" in destination
            or ".." in relative.parts
            or relative.is_absolute()
            or not target.resolve().is_relative_to(root)
        ):
            errors.append("Unsafe path in upstream manifest: " + destination)
            continue
        source = destination.removeprefix(".agents/")
        if (
            not isinstance(record, dict)
            or record.get("source") != source
            or not (
                source == "LICENSE"
                or source.startswith("references/")
                or any(source.startswith("skills/" + name + "/") for name in SKILLS)
            )
        ):
            errors.append("Invalid upstream source mapping: " + destination)
            continue
        try:
            data = target.read_bytes()
        except OSError as error:
            errors.append("Cannot read " + destination + ": " + str(error))
            continue
        contents[destination] = data
        blob = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest()
        if hashlib.sha256(data).hexdigest() != record.get(
            "sha256"
        ) or blob != record.get("git_blob_sha1"):
            errors.append("Upstream hash mismatch: " + destination)
        if not destination.endswith(".md"):
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeError:
            errors.append("Invalid UTF-8: " + destination)
            continue
        if destination.endswith("/SKILL.md"):
            header = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
            if (
                not header
                or not re.search(
                    r"(?m)^name: " + re.escape(target.parent.name) + r"$", header[1]
                )
                or not re.search(r"(?m)^description: \S", header[1])
            ):
                errors.append("Invalid skill discovery metadata: " + destination)
        for reference in set(REFERENCES.findall(text)):
            resolved = (target.parent / reference).resolve()
            if not resolved.is_relative_to(root) or not resolved.is_file():
                errors.append("Broken reference in " + destination + ": " + reference)

    if archive is not None:
        try:
            archive = Path(archive)
            if (
                hashlib.sha256(archive.read_bytes()).hexdigest()
                != manifest["archive"]["sha256"]
            ):
                return errors + ["Upstream archive hash mismatch"]
            with zipfile.ZipFile(archive) as bundle:
                prefix = "agent-skills-" + commit + "/"
                sources = {
                    name[len(prefix) :]
                    for name in bundle.namelist()
                    if name.startswith(prefix) and not name.endswith("/")
                }
                selected = {
                    name
                    for name in sources
                    if name == "LICENSE"
                    or name.startswith("references/")
                    or any(name.startswith("skills/" + skill + "/") for skill in SKILLS)
                }
                if selected != {files[path]["source"] for path in contents}:
                    errors.append(
                        "Selected upstream archive inventory differs from manifest"
                    )
                for destination, data in contents.items():
                    source = files[destination]["source"]
                    if source not in sources or bundle.read(prefix + source) != data:
                        errors.append(
                            "Upstream archive content mismatch: " + destination
                        )
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            errors.append("Cannot verify upstream archive: " + str(error))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive", type=Path, help="Compare with the pinned upstream ZIP"
    )
    args = parser.parse_args()
    errors = verify(Path(__file__).resolve().parents[1], args.archive)
    if errors:
        for error in errors:
            print("FAIL: " + error)
        return 1
    print(
        "PASS: six skills; upstream hashes, metadata, layout, and reference paths verified."
    )
    if args.archive is not None:
        print(
            "PASS: pinned archive digest, selected inventory, and upstream bytes verified."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
