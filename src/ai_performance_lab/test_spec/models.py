from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ContractModel(BaseModel):
    """Base model for strict Test Spec validation."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
    )


class RequestSpec(ContractModel):
    """Describe the HTTP request under test."""

    method: Literal["GET"]
    url: HttpUrl


class LoadSpec(ContractModel):
    """Describe the deterministic M0 load model."""

    threads: int = Field(ge=1, le=1000)
    ramp_up_seconds: int = Field(ge=0, le=3600)
    duration_seconds: int = Field(ge=1, le=86400)

    @model_validator(mode="after")
    def validate_ramp_up(self) -> Self:
        if self.ramp_up_seconds > self.duration_seconds:
            raise ValueError(
                "ramp_up_seconds must not exceed duration_seconds"
            )

        return self


class AcceptanceSpec(ContractModel):
    """Describe deterministic acceptance thresholds."""

    min_rps: float = Field(gt=0)
    min_samples: int = Field(ge=1)
    p95_ms: float = Field(gt=0)
    success_rate: float = Field(ge=0, le=100)


class TestSpec(ContractModel):
    """Top-level M0 performance test input contract."""

    version: Literal["1.0"]
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    request: RequestSpec
    load: LoadSpec
    acceptance: AcceptanceSpec