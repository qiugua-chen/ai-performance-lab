from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JTLSample:
    """一条已解析的 JMeter 样本。"""

    timestamp_ms: int
    elapsed_ms: int
    label: str
    response_code: str
    success: bool


@dataclass(frozen=True)
class JTLDocument:
    """已解析的 JTL 文件及其全部已校验样本。"""

    source_path: Path
    samples: tuple[JTLSample, ...]

    @property
    def sample_count(self) -> int:
        return len(self.samples)