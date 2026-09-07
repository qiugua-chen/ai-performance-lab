from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ContractModel(BaseModel):
    """严格校验测试规格的模型基类。"""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
    )


class RequestSpec(ContractModel):
    """描述被测 HTTP 请求。"""

    method: Literal["GET"]
    url: HttpUrl


class LoadSpec(ContractModel):
    """描述 M0 的线程数、Ramp-up 时间和执行时长。"""

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
    """描述性能验收阈值。"""

    min_rps: float = Field(gt=0)
    min_samples: int = Field(ge=1)
    p95_ms: float = Field(gt=0)
    success_rate: float = Field(ge=0, le=100)


class TestSpec(ContractModel):
    """M0 性能测试的顶层输入模型。"""

    version: Literal["1.0"]
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    request: RequestSpec
    load: LoadSpec
    acceptance: AcceptanceSpec