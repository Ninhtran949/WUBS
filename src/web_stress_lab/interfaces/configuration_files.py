"""Bounded local config reads and paths, with no referenced-file contents read."""

import json
import os
import re
import stat
from pathlib import Path, PureWindowsPath

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from web_stress_lab.domain.errors import ConfigurationError, InputIssue

MAX_CONFIG_BYTES = 65536
MAX_NODES = 4096
MAX_DEPTH = 32
_PORTABLE_PATH = re.compile(r"[A-Za-z0-9_. -]+(?:/[A-Za-z0-9_. -]+)*")
_DEVICES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}
_YAML_TAGS = {
    f"tag:yaml.org,2002:{name}"
    for name in ("map", "seq", "str", "int", "float", "bool", "null")
}


def _failure(field: str, code: str) -> ConfigurationError:
    return ConfigurationError([InputIssue(field, code)])


def _device(part: str) -> bool:
    return part.split(".", 1)[0].upper() in _DEVICES


def _guard_components(path: Path, field: str) -> os.stat_result | None:
    info = None
    for candidate in (*reversed(path.parents), path):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            return None
        except OSError:
            raise _failure(field, "path_unreadable") from None
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise _failure(field, "reparse_path_disabled")
    return info


def reference_path(
    base: Path, value: str, field: str, *, directory: bool = False
) -> Path:
    if not _PORTABLE_PATH.fullmatch(value) or any(
        part in {".", ".."}
        or part != part.strip()
        or part.endswith(".")
        or _device(part)
        for part in value.split("/")
    ):
        raise _failure(field, "unsafe_relative_path")
    path = base / value
    if not directory and path.suffix.lower() != ".json":
        raise _failure(field, "catalog_requires_json")
    info = _guard_components(path, field)
    if info is not None:
        expected = (
            stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
        )
        if not expected:
            raise _failure(field, "invalid_path_type")
    return path


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _failure("$", "duplicate_mapping_key")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise _failure("$", "nonfinite_number")


def _bound_json(value: object) -> None:
    stack = [(value, 0)]
    count = 0
    while stack:
        current, depth = stack.pop()
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise _failure("$", "document_complexity_limit")
        if isinstance(current, dict):
            stack.extend((value, depth + 1) for value in current.values())
        elif isinstance(current, list):
            stack.extend((value, depth + 1) for value in current)


def _check_yaml(node: Node) -> None:
    stack = [(node, 0)]
    seen: set[int] = set()
    while stack:
        current, depth = stack.pop()
        if id(current) in seen:
            raise _failure("$", "yaml_alias_disabled")
        seen.add(id(current))
        if depth > MAX_DEPTH or len(seen) > MAX_NODES:
            raise _failure("$", "document_complexity_limit")
        if current.tag not in _YAML_TAGS:
            raise _failure("$", "unsupported_yaml_tag")
        if isinstance(current, MappingNode):
            keys: set[str] = set()
            for key, value in current.value:
                if (
                    not isinstance(key, ScalarNode)
                    or key.tag != "tag:yaml.org,2002:str"
                ):
                    raise _failure("$", "mapping_key_requires_string")
                if key.value in keys:
                    raise _failure("$", "duplicate_mapping_key")
                keys.add(key.value)
                stack.extend(((key, depth + 1), (value, depth + 1)))
        elif isinstance(current, SequenceNode):
            stack.extend((value, depth + 1) for value in current.value)


def read_document(path: Path) -> tuple[object, Path]:
    raw = str(path)
    windows = PureWindowsPath(raw)
    if (
        raw.startswith(("\\\\", "//"))
        or "://" in raw
        or "\x00" in raw
        or (windows.drive and (os.name != "nt" or not windows.is_absolute()))
    ):
        raise _failure("$", "local_config_required")
    path = Path(os.path.abspath(path))
    if any(":" in part or _device(part) for part in path.parts[1:]):
        raise _failure("$", "unsafe_config_path")
    suffix = path.suffix.lower()
    if suffix not in {".json", ".yaml", ".yml"}:
        raise _failure("$", "unsupported_format")
    info = _guard_components(path, "$")
    if info is None or not stat.S_ISREG(info.st_mode):
        raise _failure("$", "regular_config_required")
    try:
        with path.open("rb") as source:
            data = source.read(MAX_CONFIG_BYTES + 1)
        if len(data) > MAX_CONFIG_BYTES:
            raise _failure("$", "config_size_limit")
        text = data.decode("utf-8-sig")
        document: object
        if suffix == ".json":
            document = json.loads(
                text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant
            )
            _bound_json(document)
        else:
            loader = yaml.SafeLoader(text)
            try:
                node = loader.get_single_node()
                if node is None:
                    document = None
                else:
                    _check_yaml(node)
                    try:
                        document = loader.construct_document(node)
                    except (KeyError, IndexError, OverflowError):
                        raise _failure("$", "unreadable_or_malformed_config") from None
            finally:
                loader.dispose()
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, RecursionError):
        raise _failure("$", "unreadable_or_malformed_config") from None
    return document, path.parent
