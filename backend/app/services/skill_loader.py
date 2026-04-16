"""Skills dynamic loading: upload zip → extract → install deps → importlib hot-load → register."""
import json
import sys
import zipfile
import importlib.util
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from app.mcp.tools.base import ToolBase
from app.mcp import registry

SKILLS_STORE = Path(__file__).parent.parent.parent / "skills_store"
SKILLS_STORE.mkdir(exist_ok=True)

# Tracks which sys.modules key belongs to each skill, for clean unload
_skill_module_keys: dict[str, str] = {}


@dataclass
class SkillMeta:
    name: str
    version: str
    description: str
    entry: str                    # "module_filename:ClassName"
    requirements: list[str] = field(default_factory=list)


def read_meta_from_zip(zip_path: Path) -> SkillMeta:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("meta.json") as f:
            data = json.load(f)
    return SkillMeta(
        name=data["name"],
        version=data.get("version", "0.1.0"),
        description=data.get("description", ""),
        entry=data["entry"],
        requirements=data.get("requirements", []),
    )


def install_skill_package(zip_path: Path) -> tuple[SkillMeta, Path]:
    """Extract zip to skills_store/{name}/, install requirements, return meta + skill_dir."""
    meta = read_meta_from_zip(zip_path)
    skill_dir = SKILLS_STORE / meta.name
    skill_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(skill_dir)

    if meta.requirements:
        result = subprocess.run(
            ["uv", "pip", "install", "--quiet"] + meta.requirements,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to install requirements: {result.stderr}")

    return meta, skill_dir


def load_and_register(skill_dir: Path, entry: str, skill_name: str) -> ToolBase:
    """Import the skill module, instantiate the ToolBase subclass, register it."""
    module_file_name, class_name = entry.split(":", 1)
    module_file = skill_dir / f"{module_file_name}.py"
    if not module_file.exists():
        raise FileNotFoundError(f"Skill entry file not found: {module_file}")

    module_key = f"workmate_skill_{skill_name}"
    spec = importlib.util.spec_from_file_location(module_key, module_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_key] = module
    spec.loader.exec_module(module)

    cls = getattr(module, class_name, None)
    if cls is None:
        raise AttributeError(f"Class '{class_name}' not found in {module_file}")
    if not (isinstance(cls, type) and issubclass(cls, ToolBase)):
        raise TypeError(f"'{class_name}' must be a subclass of ToolBase")

    tool = cls()
    _skill_module_keys[skill_name] = module_key
    registry.register(tool)
    return tool


def unload_skill(name: str) -> None:
    """Unregister the skill and remove its module from sys.modules."""
    registry.unregister(name)
    module_key = _skill_module_keys.pop(name, None)
    if module_key:
        sys.modules.pop(module_key, None)


def reload_skills_from_store(enabled_skills: list[tuple[str, str, str]]) -> None:
    """Called at startup. enabled_skills: list of (name, package_path, entry_point)."""
    for name, package_path, entry_point in enabled_skills:
        skill_dir = Path(package_path) if package_path else SKILLS_STORE / name
        if not skill_dir.exists():
            continue
        try:
            load_and_register(skill_dir, entry_point, name)
        except Exception as exc:
            # Log but don't crash startup
            print(f"[skill_loader] Failed to load skill '{name}': {exc}")
