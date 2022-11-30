from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple


class BaseStorage(Protocol):
    def filter(self, criteria: FilterQuery):
        ...

    def getSummary(self, criteria: FilterQuery):
        ...

    def insert(self, measurement):
        ...

    def delete(self, measurementId):
        ...

    def truncate(self):
        ...


@dataclass
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
