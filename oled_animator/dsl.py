"""
DSL Parser — reads YAML scene definitions and builds Animation objects.
"""

import yaml
import os
from .engine import Animation


REQUIRED_SCREEN_FIELDS = {"width", "height", "fps", "frames"}
VALID_ELEMENT_TYPES = {"rect", "circle", "line", "text", "sprite"}


class DSLError(Exception):
    """Raised when a YAML scene file has invalid structure."""
    pass


def parse_scene(yaml_path: str) -> dict:
    """Parse a YAML scene file and return a validated scene dict.

    Returns:
        {
            "animation": Animation instance (ready to render),
            "output": dict with export options,
            "base_dir": directory of the YAML file (for relative paths)
        }
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        scene = yaml.safe_load(f)

    base_dir = os.path.dirname(os.path.abspath(yaml_path))

    screen = _validate_screen(scene)
    elements = _validate_elements(scene, base_dir)
    output = scene.get("output", {})

    anim = Animation(
        width=screen["width"],
        height=screen["height"],
        fps=screen["fps"],
        total_frames=screen["frames"],
    )

    for elem in elements:
        anim.add_element(elem)

    return {
        "animation": anim,
        "output": output,
        "base_dir": base_dir,
    }


def _validate_screen(scene: dict) -> dict:
    screen = scene.get("screen")
    if not screen:
        raise DSLError("Missing 'screen' section in YAML.")

    missing = REQUIRED_SCREEN_FIELDS - set(screen.keys())
    if missing:
        raise DSLError(f"Missing screen fields: {missing}")

    w, h = screen["width"], screen["height"]
    if w % 8 != 0:
        raise DSLError(f"Screen width ({w}) must be divisible by 8.")
    if h % 8 != 0:
        raise DSLError(f"Screen height ({h}) must be divisible by 8.")

    return screen


def _validate_elements(scene: dict, base_dir: str) -> list:
    elements = scene.get("elements", [])
    validated = []

    for i, elem in enumerate(elements):
        elem_type = elem.get("type")
        if not elem_type:
            raise DSLError(f"Element #{i} missing 'type' field.")
        if elem_type not in VALID_ELEMENT_TYPES:
            raise DSLError(
                f"Element #{i} has invalid type '{elem_type}'. "
                f"Valid: {VALID_ELEMENT_TYPES}"
            )

        props = dict(elem.get("props", {}))

        if elem_type == "sprite" and "src" in props:
            src = props["src"]
            if not os.path.isabs(src):
                props["src"] = os.path.join(base_dir, src)

        if elem_type == "text" and "font_path" in props:
            fp = props["font_path"]
            if fp and not os.path.isabs(fp):
                props["font_path"] = os.path.join(base_dir, fp)

        validated.append({
            "type": elem_type,
            "id": elem.get("id", f"element_{i}"),
            "props": props,
            "keyframes": elem.get("keyframes", []),
        })

    return validated
