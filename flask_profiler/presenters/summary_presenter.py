from typing import Any, List

from flask_profiler.storage.base import Summary


class SummaryPresenter:
    def present_summaries(self, summaries: List[Summary]) -> Any:
        return {
            "measurements": [
                dict(
                    method=summary.method,
                    name=summary.name,
                    count=summary.count,
                    avgElapsed=summary.avg_elapsed,
                    minElapsed=summary.min_elapsed,
                    maxElapsed=summary.max_elapsed,
                )
                for summary in summaries
            ]
        }
