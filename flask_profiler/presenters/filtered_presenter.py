from typing import Any, List

from flask_profiler.storage.base import Record


class FilteredPresenter:
    def present_filtered_measurements(self, measurements: List[Record]) -> Any:
        return {
            "measurements": [
                dict(
                    id=measurement.id,
                    startedAt=measurement.startedAt,
                    endedAt=measurement.endedAt,
                    elapsed=measurement.elapsed,
                    args=measurement.args,
                    kwargs=measurement.kwargs,
                    method=measurement.method,
                    context=measurement.context.serialize_to_json(),
                    name=measurement.name,
                )
                for measurement in measurements
            ]
        }
