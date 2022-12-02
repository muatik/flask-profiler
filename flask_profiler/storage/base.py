from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple


class BaseStorage(Protocol):
    def filter(self, criteria: FilterQuery) -> List[Record]:
        ...

    def getSummary(self, criteria: FilterQuery) -> List[Summary]:
        ...

    def get(self, measurementId) -> Record:
        ...

    def insert(self, measurement: Measurement) -> None:
        ...

    def delete(self, measurement_id: int) -> None:
        ...

    def truncate(self) -> bool:
        ...

    def getTimeseries(
        self, startedAt: float, endedAt: float, interval: str
    ) -> Dict[Tuple[datetime, str], int]:
        ...

    def getMethodDistribution(self, startedAt: float, endedAt: float) -> Dict[str, int]:
        ...


@dataclass(kw_only=True)
class RequestMetadata:
    url: str
    args: Dict[str, str]
    form: Dict[str, str]
    headers: Dict[str, str]
    endpoint_name: str
    client_address: str

    def serialize_to_json(self) -> Dict[str, Any]:
        return asdict(self)


DECIMAL_PLACES = 6


@dataclass(kw_only=True)
class Measurement:
    """represents an endpoint measurement"""

    context: RequestMetadata
    name: str
    method: str
    args: List[str]
    kwargs: Dict[str, str]
    startedAt: float
    endedAt: float

    def serialize_to_json(self):
        return {
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "method": self.method,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed,
            "context": self.context.serialize_to_json(),
        }

    def __str__(self):
        return str(self.serialize_to_json())

    @property
    def elapsed(self) -> float:
        return max(
            round(self.endedAt - self.startedAt, DECIMAL_PLACES),
            0.0,
        )


@dataclass(kw_only=True)
class FilterQuery:
    limit: int
    skip: int
    sort: Tuple[str, str]
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None
    elapsed: Optional[float] = None
    name: Optional[str] = None
    method: Optional[str] = None
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None


@dataclass(kw_only=True)
class Record:
    id: int
    name: str
    startedAt: float
    endedAt: float
    elapsed: float
    args: List[str]
    kwargs: Dict[str, Any]
    method: str
    context: RequestMetadata

    def serialize_to_json(self) -> Any:
        data = {
            "id": self.id,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed,
            "args": tuple(self.args),
            "kwargs": self.kwargs,
            "method": self.method,
            "context": self.context.serialize_to_json(),
            "name": self.name,
        }

        return data


@dataclass(kw_only=True)
class Summary:
    method: str
    name: str
    count: int
    min_elapsed: float
    max_elapsed: float
    avg_elapsed: float

    def serialize_to_json(self) -> Any:
        return dict(
            method=self.method,
            name=self.name,
            count=self.count,
            minElapsed=self.min_elapsed,
            maxElapsed=self.max_elapsed,
            avgElapsed=self.avg_elapsed,
        )
