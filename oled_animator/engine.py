"""
Animation Engine — timeline, keyframes, easing interpolation, frame rendering.
"""

from .canvas import Canvas
from .primitives import draw_rect, draw_circle, draw_line, draw_text, draw_sprite
from .easing import get_easing


DRAW_DISPATCH = {
    "rect": draw_rect,
    "circle": draw_circle,
    "line": draw_line,
    "text": draw_text,
    "sprite": draw_sprite,
}

ANIMATABLE_PROPS = {"x", "y", "cx", "cy", "r", "w", "h", "x1", "y1", "x2", "y2", "font_size"}


class Animation:
    """Core animation engine. Manages elements, keyframes, and rendering."""

    def __init__(self, width: int, height: int, fps: int, total_frames: int):
        self.width = width
        self.height = height
        self.fps = fps
        self.total_frames = total_frames
        self.elements = []

    def add_element(self, element: dict):
        """Add an element definition.

        element = {
            "type": "circle",
            "id": "ball",
            "props": {"cx": 10, "cy": 32, "r": 5, "fill": True},
            "keyframes": [
                {"frame": 0, "cx": 10, "easing": "ease-in-out"},
                {"frame": 20, "cx": 100},
            ]
        }
        """
        self.elements.append(element)

    def _interpolate(self, element: dict, frame: int) -> dict:
        """Resolve all properties for an element at a given frame."""
        props = dict(element.get("props", {}))
        keyframes = element.get("keyframes", [])

        if not keyframes:
            return props

        sorted_kf = sorted(keyframes, key=lambda k: k["frame"])

        for prop_name in ANIMATABLE_PROPS:
            kf_with_prop = [k for k in sorted_kf if prop_name in k]
            if not kf_with_prop:
                continue

            if frame <= kf_with_prop[0]["frame"]:
                props[prop_name] = kf_with_prop[0][prop_name]
                continue

            if frame >= kf_with_prop[-1]["frame"]:
                props[prop_name] = kf_with_prop[-1][prop_name]
                continue

            for i in range(len(kf_with_prop) - 1):
                kf_start = kf_with_prop[i]
                kf_end = kf_with_prop[i + 1]

                if kf_start["frame"] <= frame <= kf_end["frame"]:
                    span = kf_end["frame"] - kf_start["frame"]
                    if span == 0:
                        t = 1.0
                    else:
                        t = (frame - kf_start["frame"]) / span

                    easing_name = kf_start.get("easing", "linear")
                    easing_fn = get_easing(easing_name)
                    eased_t = easing_fn(t)

                    val_start = kf_start[prop_name]
                    val_end = kf_end[prop_name]
                    props[prop_name] = val_start + (val_end - val_start) * eased_t
                    break

        return props

    def render_frame(self, frame_index: int) -> Canvas:
        """Render a single frame, returning a Canvas."""
        canvas = Canvas(self.width, self.height)

        for elem in self.elements:
            props = self._interpolate(elem, frame_index)
            elem_type = elem["type"]

            if elem_type == "rect":
                draw_rect(
                    canvas,
                    x=int(props.get("x", 0)),
                    y=int(props.get("y", 0)),
                    w=int(props.get("w", 10)),
                    h=int(props.get("h", 10)),
                    fill=props.get("fill", True),
                    anti_alias=props.get("anti_alias", False),
                )

            elif elem_type == "circle":
                draw_circle(
                    canvas,
                    cx=int(props.get("cx", 0)),
                    cy=int(props.get("cy", 0)),
                    r=int(props.get("r", 5)),
                    fill=props.get("fill", True),
                    anti_alias=props.get("anti_alias", False),
                )

            elif elem_type == "line":
                draw_line(
                    canvas,
                    x1=int(props.get("x1", 0)),
                    y1=int(props.get("y1", 0)),
                    x2=int(props.get("x2", 0)),
                    y2=int(props.get("y2", 0)),
                    anti_alias=props.get("anti_alias", False),
                )

            elif elem_type == "text":
                draw_text(
                    canvas,
                    x=int(props.get("x", 0)),
                    y=int(props.get("y", 0)),
                    text=str(props.get("text", "")),
                    font_size=int(props.get("font_size", 10)),
                    font_path=props.get("font_path"),
                )

            elif elem_type == "sprite":
                draw_sprite(
                    canvas,
                    x=int(props.get("x", 0)),
                    y=int(props.get("y", 0)),
                    src=str(props.get("src", "")),
                    dithering=props.get("dithering", False),
                )

        return canvas

    def render_all(self) -> list:
        """Render all frames, returning list of Canvas."""
        return [self.render_frame(i) for i in range(self.total_frames)]
