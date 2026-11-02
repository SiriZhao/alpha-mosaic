"""Reject existing symbolic-link/junction redirection at local write boundaries."""

import os
from pathlib import Path


def unredirected(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    if absolute.is_symlink() or absolute.is_junction() or absolute.resolve() != absolute:
        raise ValueError("local research path is redirected by a symbolic link or junction")
    return absolute


def contained_child(root: Path, name: str) -> Path:
    if name in {"", ".", ".."} or Path(name).name != name:
        raise ValueError("a single local artifact name is required")
    root = unredirected(root)
    path = unredirected(root / name)
    if path.parent != root:
        raise ValueError("local artifact escapes its research store")
    return path
