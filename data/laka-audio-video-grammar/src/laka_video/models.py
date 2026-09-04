from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Cue:
    index: int
    start: float
    end: float
    text: str
    tags: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class TextUnit:
    id: str
    start: float
    end: float
    text: str
    cue_ids: list[int]
    tags: dict[str, Any] = field(default_factory=dict)
    explicit_boundary: bool = False

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class SceneDraft:
    id: str
    start: float
    end: float
    text: str
    cue_ids: list[int]
    tags: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)
