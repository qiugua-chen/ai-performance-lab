from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JTLSample:
    """One parsed JMeter sample."""

    timestamp_ms: int
    elapsed_ms: int
    label: str
    response_code: str
    success: bool


@dataclass(frozen=True)
class JTLDocument:
    """A parsed JTL file and all validated samples."""

    source_path: Path
    samples: tuple[JTLSample, ...]

    @property
    def sample_count(self) -> int:
        return len(self.samples)