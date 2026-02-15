"""
Easing functions for smooth animations.

All functions take t in [0, 1] and return a value in [0, 1].
"""

import math

def linear(t: float) -> float:
    return t

def ease_in(t: float) -> float:
    return t * t

def ease_out(t: float) -> float:
    return t * (2.0 - t)

def ease_in_out(t: float) -> float:
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t

def cubic_in(t: float) -> float:
    return t * t * t

def cubic_out(t: float) -> float:
    t -= 1.0
    return t * t * t + 1.0

def cubic_in_out(t: float) -> float:
    if t < 0.5:
        return 4.0 * t * t * t
    t -= 1.0
    return 0.5 * (4.0 * t * t * t + 2.0)

def elastic(t: float) -> float:
    """Elastic ease-in: oscillates at the START, settles at end."""
    if t == 0.0 or t == 1.0:
        return t
    p = 0.3
    s = p / 4.0
    t -= 1.0
    return -(math.pow(2.0, 10.0 * t) * math.sin((t - s) * (2.0 * math.pi) / p))


def elastic_out(t: float) -> float:
    """Elastic ease-out: springs PAST the target and bounces back.
    This is the 'mochi' feel — the visually impactful one.
    """
    if t == 0.0 or t == 1.0:
        return t
    p = 0.3
    s = p / 4.0
    return math.pow(2.0, -10.0 * t) * math.sin((t - s) * (2.0 * math.pi) / p) + 1.0


def elastic_in_out(t: float) -> float:
    """Elastic ease-in-out: oscillates on both ends."""
    if t == 0.0 or t == 1.0:
        return t
    p = 0.45
    s = p / 4.0
    t = t * 2.0
    if t < 1.0:
        t -= 1.0
        return -0.5 * (math.pow(2.0, 10.0 * t) * math.sin((t - s) * (2.0 * math.pi) / p))
    t -= 1.0
    return 0.5 * (math.pow(2.0, -10.0 * t) * math.sin((t - s) * (2.0 * math.pi) / p)) + 1.0


def bounce(t: float) -> float:
    """Bounce ease-in: bounces at the START."""
    if t < 1.0 / 2.75:
        return 7.5625 * t * t
    elif t < 2.0 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def bounce_out(t: float) -> float:
    """Bounce ease-out: ball-drop bounce, settles at the target."""
    t = 1.0 - t
    return 1.0 - bounce(t)


EASING_FUNCTIONS = {
    "linear": linear,
    "ease-in": ease_in,
    "ease-out": ease_out,
    "ease-in-out": ease_in_out,
    "cubic-in": cubic_in,
    "cubic-out": cubic_out,
    "cubic-in-out": cubic_in_out,
    "elastic": elastic,
    "elastic-out": elastic_out,
    "elastic-in-out": elastic_in_out,
    "bounce": bounce,
    "bounce-out": bounce_out,
}


def get_easing(name: str):
    """Get easing function by name. Falls back to linear."""
    return EASING_FUNCTIONS.get(name, linear)
