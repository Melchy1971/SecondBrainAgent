from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import json
import sys
import sysconfig
from pathlib import Path
from typing import Any, Iterable


IGNORE_DIR_NAMES: set[str] = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "release",
    "venv",
    ".venv",
    "env",
    ".env",
}

PACKAGE_NAME_ALIASES: dict[str, str] = {
    "PIL": "Pillow",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "dotenv": "python-dotenv",
    "fitz": "PyMuPDF",
    "google": "google-generativeai or google-api-python-client",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
}

OPTIONAL_PROVIDER_MODULES: set[str] = {
    "anthropic",
    "google",
    "groq",
    "ollama",
    "openai",
}


@dataclass(frozen=True)
class ImportOccurrence:
    module: str
    file: str
    line: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DependencyInventory:
    ok: bool
    project_root: str
    python_version: str
    scanned_files: int
    internal_roots: list[str]
    standard_library: list[str]
    internal: list[str]
    external: list[str]
    optional_provider: list[str]
    unknown: list[str]
    occurrences: list[ImportOccurrence]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "project_root": self.project_root,
            "python_version": self.python_version,
            "scanned_files": self.scanned_files,
            "internal_roots": self.internal_roots,
            "summary": {
                "standard_library": len(self.standard_library),
                "internal": len(self.internal),
                "external": len(self.external),
                "optional_provider": len(self.optional_provider),
                "unknown": len(self.unknown),
                "warnings": len(self.warnings),
            },
            "standard_library": self.standard_library,
            "internal": self.internal,
            "external": self.external,
            "optional_provider": self.optional_provider,
            "unknown": self.unknown,
            "requirements_suggestion": render_requirements(self.external),
            "optional_requirements_suggestion": render_requirements(self.optional_provider),
            "warnings": self.warnings,
            "occurrences": [item.to_dict() for item in self.occurrences],
        }


def _stdlib_modules() -> set[str]:
    names = set(getattr(sys, "stdlib_module_names", set()))
    names.update(sys.builtin_module_names)
    names.update({"typing_extensions"})
    return names


def _site_package_paths() -> set[str]:
    raw_paths = {
        sysconfig.get_paths().get("purelib"),
        sysconfig.get_paths().get("platlib"),
    }
    return {str(Path(path).resolve()) for path in raw_paths if path}


def _iter_python_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if any(part in IGNORE_DIR_NAMES for part in path.parts):
            continue
        yield path


def _top_level(name: str) -> str:
    return name.split(".", 1)[0]


def _extract_imports(path: Path, root: Path) -> list[ImportOccurrence]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        rel = path.relative_to(root).as_posix()
        return [ImportOccurrence(module=f"<syntax-error:{exc.msg}>", file=rel, line=exc.lineno or 0)]
    except UnicodeDecodeError:
        rel = path.relative_to(root).as_posix()
        return [ImportOccurrence(module="<decode-error>", file=rel, line=0)]

    occurrences: list[ImportOccurrence] = []
    rel = path.relative_to(root).as_posix()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                occurrences.append(ImportOccurrence(module=_top_level(alias.name), file=rel, line=node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level and not node.module:
                continue
            if node.level and node.module:
                # Relative import. Treat as internal and normalize to declared module root.
                occurrences.append(ImportOccurrence(module=_top_level(node.module), file=rel, line=node.lineno))
            elif node.module:
                occurrences.append(ImportOccurrence(module=_top_level(node.module), file=rel, line=node.lineno))
    return occurrences


def _internal_roots(root: Path) -> set[str]:
    roots = {path.name for path in root.iterdir() if path.is_dir() and (path / "__init__.py").exists()}
    for path in root.glob("*.py"):
        roots.add(path.stem)
    return roots


def _classify(module: str, internal_roots: set[str], stdlib: set[str], site_paths: set[str]) -> str:
    if module.startswith("<"):
        return "unknown"
    if module in internal_roots:
        return "internal"
    if module in stdlib:
        return "standard_library"
    if module in OPTIONAL_PROVIDER_MODULES:
        return "optional_provider"
    spec = None
    try:
        import importlib.util

        spec = importlib.util.find_spec(module)
    except (ImportError, AttributeError, ValueError):
        spec = None
    if spec is not None and spec.origin:
        origin = str(Path(spec.origin).resolve())
        if any(origin.startswith(site_path) for site_path in site_paths):
            return "external"
        return "standard_library"
    return "external"


def render_requirements(modules: Iterable[str]) -> list[str]:
    lines = []
    for module in sorted(set(modules)):
        lines.append(PACKAGE_NAME_ALIASES.get(module, module))
    return lines


def build_dependency_inventory(project_root: str | Path, *, write_report: bool = False) -> DependencyInventory:
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        return DependencyInventory(
            ok=False,
            project_root=str(root),
            python_version=sys.version.split()[0],
            scanned_files=0,
            internal_roots=[],
            standard_library=[],
            internal=[],
            external=[],
            optional_provider=[],
            unknown=[],
            occurrences=[],
            warnings=["project root is missing or not a directory"],
        )

    stdlib = _stdlib_modules()
    site_paths = _site_package_paths()
    internal = _internal_roots(root)
    occurrences: list[ImportOccurrence] = []
    scanned_files = 0
    for path in _iter_python_files(root):
        scanned_files += 1
        occurrences.extend(_extract_imports(path, root))

    buckets: dict[str, set[str]] = {
        "standard_library": set(),
        "internal": set(),
        "external": set(),
        "optional_provider": set(),
        "unknown": set(),
    }
    for occurrence in occurrences:
        classification = _classify(occurrence.module, internal, stdlib, site_paths)
        buckets[classification].add(occurrence.module)

    warnings: list[str] = []
    if buckets["unknown"]:
        warnings.append("some imports could not be parsed or classified")
    if buckets["external"]:
        warnings.append("external imports detected; compare requirements-runtime.txt before release")
    if not scanned_files:
        warnings.append("no python files scanned")

    report = DependencyInventory(
        ok=not buckets["unknown"] and scanned_files > 0,
        project_root=str(root),
        python_version=sys.version.split()[0],
        scanned_files=scanned_files,
        internal_roots=sorted(internal),
        standard_library=sorted(buckets["standard_library"]),
        internal=sorted(buckets["internal"]),
        external=sorted(buckets["external"]),
        optional_provider=sorted(buckets["optional_provider"]),
        unknown=sorted(buckets["unknown"]),
        occurrences=sorted(occurrences, key=lambda item: (item.module, item.file, item.line)),
        warnings=warnings,
    )

    if write_report:
        target = root / "release" / "dependency_inventory_latest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    return report
