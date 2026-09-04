from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .utils import clamp, ffprobe_duration, json_safe


@dataclass
class AudioAnalysis:
    path: Path
    sample_rate: int
    duration: float
    frame_hop_seconds: float
    frame_times: np.ndarray
    rms: np.ndarray
    rms_normalized: np.ndarray
    silence_mask: np.ndarray
    onsets: list[float]
    silences: list[dict[str, float]]
    sections: list[float]
    summary: dict[str, Any]

    def interval_features(self, start: float, end: float) -> dict[str, Any]:
        start = max(0.0, float(start))
        end = max(start + 1e-6, float(end))
        mask = (self.frame_times >= start) & (self.frame_times < end)
        if not np.any(mask):
            idx = int(np.clip(round(start / max(self.frame_hop_seconds, 1e-6)), 0, max(0, len(self.rms) - 1)))
            values = self.rms_normalized[idx:idx + 1]
            silence_values = self.silence_mask[idx:idx + 1]
        else:
            values = self.rms_normalized[mask]
            silence_values = self.silence_mask[mask]
        local_onsets = [t for t in self.onsets if start <= t < end]
        mean_energy = float(np.mean(values)) if len(values) else 0.0
        peak_energy = float(np.max(values)) if len(values) else 0.0
        silence_ratio = float(np.mean(silence_values)) if len(silence_values) else 0.0
        duration = end - start
        onset_rate = len(local_onsets) / max(duration, 1e-6)
        if mean_energy >= 0.72 or onset_rate >= 2.0:
            band = "high"
        elif mean_energy <= 0.28 and onset_rate < 0.8:
            band = "low"
        else:
            band = "medium"
        return {
            "mean_energy": round(mean_energy, 4),
            "peak_energy": round(peak_energy, 4),
            "silence_ratio": round(silence_ratio, 4),
            "onset_count": len(local_onsets),
            "onset_rate": round(onset_rate, 4),
            "energy_band": band,
        }

    def public_summary(self) -> dict[str, Any]:
        return json_safe(self.summary)


def _decode_f32(path: Path, sample_rate: int) -> np.ndarray:
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
        "-vn", "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "pipe:1",
    ]
    try:
        proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg is required but was not found on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg could not decode {path}: {message}") from exc
    samples = np.frombuffer(proc.stdout, dtype=np.float32)
    if samples.size == 0:
        raise RuntimeError(f"Audio decoded to zero samples: {path}")
    return samples


def _frame_rms(samples: np.ndarray, frame: int, hop: int) -> tuple[np.ndarray, np.ndarray]:
    if samples.size < frame:
        padded = np.pad(samples, (0, frame - samples.size))
        return np.array([float(np.sqrt(np.mean(padded * padded) + 1e-12))]), np.array([0])
    starts = np.arange(0, samples.size - frame + 1, hop, dtype=np.int64)
    power = np.asarray(samples, dtype=np.float64) ** 2
    cumulative = np.concatenate(([0.0], np.cumsum(power)))
    sums = cumulative[starts + frame] - cumulative[starts]
    rms = np.sqrt(np.maximum(sums / frame, 1e-12))
    return rms.astype(np.float32), starts


def _group_boolean_intervals(mask: np.ndarray, hop_seconds: float, min_seconds: float) -> list[dict[str, float]]:
    result: list[dict[str, float]] = []
    if mask.size == 0:
        return result
    padded = np.concatenate(([False], mask.astype(bool), [False]))
    changes = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    for s, e in zip(starts, ends):
        start = float(s * hop_seconds)
        end = float(e * hop_seconds)
        if end - start >= min_seconds:
            result.append({"start": round(start, 4), "end": round(end, 4), "duration": round(end - start, 4)})
    return result


def _select_onsets(envelope: np.ndarray, times: np.ndarray, min_gap: float) -> list[float]:
    if envelope.size < 4:
        return []
    smooth = np.convolve(envelope, np.ones(5) / 5.0, mode="same")
    diff = np.maximum(0.0, np.diff(smooth, prepend=smooth[0]))
    positive = diff[diff > 0]
    if positive.size == 0:
        return []
    threshold = max(float(np.percentile(positive, 87)), float(np.mean(positive) + 0.8 * np.std(positive)))
    candidates = np.flatnonzero(diff >= threshold)
    result: list[float] = []
    last = -1e9
    for idx in candidates:
        t = float(times[min(idx, len(times) - 1)])
        if t - last >= min_gap:
            result.append(round(t, 4))
            last = t
    return result


def _estimate_tempo(onsets: list[float]) -> float | None:
    if len(onsets) < 4:
        return None
    intervals = np.diff(np.array(onsets, dtype=float))
    intervals = intervals[(intervals >= 0.25) & (intervals <= 1.5)]
    if intervals.size < 3:
        return None
    median = float(np.median(intervals))
    bpm = 60.0 / max(median, 1e-6)
    while bpm < 55:
        bpm *= 2
    while bpm > 190:
        bpm /= 2
    return round(bpm, 2)


def _resample_bars(values: np.ndarray, count: int) -> list[float]:
    if count <= 0:
        return []
    if values.size == 0:
        return [0.0] * count
    edges = np.linspace(0, values.size, count + 1).astype(int)
    bars = []
    for i in range(count):
        chunk = values[edges[i]:max(edges[i] + 1, edges[i + 1])]
        bars.append(round(float(np.mean(chunk)) if chunk.size else 0.0, 4))
    return bars


def analyze_audio(path: str | Path, config: dict[str, Any]) -> AudioAnalysis:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {p}")
    sample_rate = int(config.get("sample_rate", 16000))
    frame_ms = float(config.get("frame_ms", 40))
    hop_ms = float(config.get("hop_ms", 20))
    frame = max(64, int(sample_rate * frame_ms / 1000.0))
    hop = max(32, int(sample_rate * hop_ms / 1000.0))
    hop_seconds = hop / sample_rate
    samples = _decode_f32(p, sample_rate)
    measured_duration = samples.size / sample_rate
    try:
        duration = max(measured_duration, ffprobe_duration(p))
    except RuntimeError:
        duration = measured_duration
    rms, starts = _frame_rms(samples, frame, hop)
    times = starts / sample_rate
    db = 20.0 * np.log10(np.maximum(rms, 1e-8))
    low = float(np.percentile(db, 8))
    high = float(np.percentile(db, 96))
    if high - low < 3:
        rms_norm = np.zeros_like(rms, dtype=np.float32)
    else:
        rms_norm = np.clip((db - low) / (high - low), 0.0, 1.0).astype(np.float32)
    configured_silence = float(config.get("silence_db", -42.0))
    adaptive_silence = float(np.max(db) - 30.0)
    silence_threshold = max(configured_silence, adaptive_silence)
    silence_mask = db <= silence_threshold
    silences = _group_boolean_intervals(silence_mask, hop_seconds, float(config.get("silence_min_seconds", 0.30)))
    onsets = _select_onsets(rms_norm, times, float(config.get("onset_min_gap_seconds", 0.18)))
    tempo = _estimate_tempo(onsets)

    boundaries = [0.0]
    for interval in silences:
        if interval["duration"] >= 0.5:
            boundaries.append((interval["start"] + interval["end"]) / 2.0)
    # Energy-change boundaries provide options when speech contains few clean silences.
    if rms_norm.size > 20:
        window = max(5, int(round(1.0 / hop_seconds)))
        smoothed = np.convolve(rms_norm, np.ones(window) / window, mode="same")
        delta = np.abs(np.diff(smoothed, prepend=smoothed[0]))
        threshold = float(np.percentile(delta, 98))
        for idx in np.flatnonzero(delta >= threshold):
            t = float(times[min(idx, len(times) - 1)])
            if all(abs(t - b) > 1.0 for b in boundaries):
                boundaries.append(t)
    boundaries.append(duration)
    boundaries = sorted({round(clamp(b, 0.0, duration), 4) for b in boundaries})

    summary = {
        "duration": round(duration, 4),
        "sample_rate": sample_rate,
        "frame_hop_seconds": round(hop_seconds, 6),
        "mean_energy": round(float(np.mean(rms_norm)), 4),
        "peak_energy": round(float(np.max(rms_norm)), 4),
        "silence_ratio": round(float(np.mean(silence_mask)), 4),
        "silence_threshold_db": round(silence_threshold, 2),
        "silences": silences,
        "onsets": onsets,
        "tempo_bpm": tempo,
        "section_boundaries": boundaries,
        "energy_bars": _resample_bars(rms_norm, int(config.get("energy_bars", 128))),
    }
    return AudioAnalysis(
        path=p,
        sample_rate=sample_rate,
        duration=duration,
        frame_hop_seconds=hop_seconds,
        frame_times=times,
        rms=rms,
        rms_normalized=rms_norm,
        silence_mask=silence_mask,
        onsets=onsets,
        silences=silences,
        sections=boundaries,
        summary=summary,
    )
