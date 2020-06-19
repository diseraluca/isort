"""Contains all logic related to placing an import within a certain section."""
import importlib
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, Optional

from isort import sections
from isort.settings import DEFAULT_CONFIG, Config
from isort.utils import exists_case_sensitive

LOCAL = "LOCALFOLDER"


def module(name: str, config: Config = DEFAULT_CONFIG) -> str:
    """Returns the section placement for the given module name."""
    return (
        _forced_separate(name, config)
        or _local(name, config)
        or _known_pattern(name, config)
        or _src_path(name, config)
        or config.default_section
    )


def _forced_separate(name: str, config: Config) -> Optional[str]:
    for forced_separate in config.forced_separate:
        # Ensure all forced_separate patterns will match to end of string
        path_glob = forced_separate
        if not forced_separate.endswith("*"):
            path_glob = "%s*" % forced_separate

        if fnmatch(name, path_glob) or fnmatch(name, "." + path_glob):
            return forced_separate

    return None


def _local(name: str, config: Config) -> Optional[str]:
    if name.startswith("."):
        return LOCAL

    return None


def _known_pattern(name: str, config: Config) -> Optional[str]:
    parts = name.split(".")
    module_names_to_check = (".".join(parts[:first_k]) for first_k in range(len(parts), 0, -1))
    for module_name_to_check in module_names_to_check:
        for pattern, placement in config.known_patterns:
            if pattern.match(module_name_to_check):
                return placement

    return None


def _src_path(name: str, config: Config) -> Optional[str]:
    for src_path in config.src_paths:
        module_path = (src_path / os.path.sep.join(name.split(".")[0])).resolve()
        if _is_module(module_path) or _is_package(module_path):
            return sections.FIRSTPARTY

    return None


def _is_module(path: Path) -> bool:
    return (
        exists_case_sensitive(str(path.with_suffix(".py")))
        or any(
            exists_case_sensitive(str(path.with_suffix(ext_suffix)))
            for ext_suffix in importlib.machinery.EXTENSION_SUFFIXES
        )
        or exists_case_sensitive(str(path / "__init__.py"))
    )


def _is_package(path: Path) -> bool:
    return exists_case_sensitive(str(path)) and path.is_dir()
