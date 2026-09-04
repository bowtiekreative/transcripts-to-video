from __future__ import annotations

import copy
from typing import Any


_MAGNITUDE_PX = {"none": 0, "micro": 8, "small": 20, "medium": 42, "large": 78, "hero": 130}
_RATE_SCALE = {"hold": 1.6, "slow": 1.25, "medium": 1.0, "fast": 0.78, "snap": 0.52, "audio_locked": 1.0}


def _apply(target: dict[str, Any], modifier: dict[str, Any]) -> None:
    for key, value in modifier.items():
        target[key] = copy.deepcopy(value)


def compile_motion(
    motion_library: dict[str, Any],
    family_name: str,
    analysis: dict[str, Any],
    scene: dict[str, Any],
    defaults: dict[str, Any],
    brand: dict[str, Any],
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    overrides = overrides or {}
    requested = str(overrides.get("motion") or family_name)
    families = motion_library.get("families", {})
    if requested not in families:
        requested = family_name if family_name in families else "reveal"
    plan = copy.deepcopy(families.get(requested, families.get("reveal", {})))
    plan["family"] = requested
    plan["phases"] = copy.deepcopy(motion_library.get("phases", {}))

    modifiers = motion_library.get("modifiers", {})
    dense_threshold = float(defaults.get("text", {}).get("dense_speech_wps", 3.2))
    if float(scene.get("words_per_second", 0.0)) > dense_threshold:
        _apply(plan, modifiers.get("dense_speech", {}))
        plan.setdefault("applied_modifiers", []).append("dense_speech")
    if analysis.get("sensitive"):
        _apply(plan, modifiers.get("sensitive_content", {}))
        plan.setdefault("applied_modifiers", []).append("sensitive_content")
    energy_band = scene.get("audio_features", {}).get("energy_band", "medium")
    if energy_band == "high" and not analysis.get("sensitive"):
        _apply(plan, modifiers.get("high_energy", {}))
        plan.setdefault("applied_modifiers", []).append("high_energy")
    elif energy_band == "low":
        _apply(plan, modifiers.get("low_energy", {}))
        plan.setdefault("applied_modifiers", []).append("low_energy")

    reduced = bool(overrides.get("reduced_motion", brand.get("motion", {}).get("reduced_motion", False)))
    if reduced:
        _apply(plan, modifiers.get("reduced_motion", {}))
        plan.setdefault("applied_modifiers", []).append("reduced_motion")
        plan["reduced_motion"] = True
    else:
        plan["reduced_motion"] = False

    # Direct LAKA-variable overrides are accepted.
    for key in (
        "magnitude", "rate", "direction", "scope", "depth", "duration", "frequency",
        "acceleration", "variability", "detectability", "reversibility", "propagation",
        "amplification", "accumulation",
    ):
        if key in overrides:
            plan[key] = overrides[key]

    magnitude = str(plan.get("magnitude", "small"))
    rate = str(plan.get("rate", "medium"))
    plan["parameters"] = {
        "travel_px": _MAGNITUDE_PX.get(magnitude, 20),
        "duration_scale": _RATE_SCALE.get(rate, 1.0),
        "camera_drift": bool(brand.get("motion", {}).get("camera_drift", True)) and not reduced,
        "energy": float(scene.get("audio_features", {}).get("mean_energy", 0.5)),
        "onset_rate": float(scene.get("audio_features", {}).get("onset_rate", 0.0)),
    }
    return plan
