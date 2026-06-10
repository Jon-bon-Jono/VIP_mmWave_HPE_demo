from pathlib import Path
import ast

BANNED_IMPORTS = {
    "rclpy",
    "vip_hpe_msgs",
    "vip_hpe_runtime",
    "torch",
    "torchvision",
    "ultralytics",
    "onnxruntime",
}

CORE_ROOT = Path(__file__).resolve().parents[2] / "src" / "vip_hpe_core" / "vip_hpe_core"


def _top_level_module(import_name: str) -> str:
    return import_name.split(".")[0]


def test_vip_hpe_core_does_not_import_ros_or_ml_dependencies():
    assert CORE_ROOT.exists(), f"Could not find vip_hpe_core at {CORE_ROOT}"

    violations = []

    for path in CORE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = _top_level_module(alias.name)
                    if top in BANNED_IMPORTS or alias.name in BANNED_IMPORTS:
                        violations.append((path, alias.name))

            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                top = _top_level_module(node.module)
                if top in BANNED_IMPORTS or node.module in BANNED_IMPORTS:
                    violations.append((path, node.module))

    assert not violations, "Banned imports in vip_hpe_core:\n" + "\n".join(
        f"{path}: {module}" for path, module in violations
    )