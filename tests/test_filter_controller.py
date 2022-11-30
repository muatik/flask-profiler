import time
from datetime import datetime
from typing import Optional
from unittest import TestCase

from flask_profiler.controllers.filter_controller import FilterController


class ParseFilterTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.clock = FakeClock()
        self.controller = FilterController(clock=self.clock)

    def test_without_data_the_default_limit_is_100(self) -> None:
        result = self.controller.parse_filter()
        assert result.limit == 100

    def test_without_data_the_default_skip_is_0(self) -> None:
        result = self.controller.parse_filter()
        assert result.skip == 0

    def test_without_data_the_default_sorting_is_by_endetAt_descending(self) -> None:
        result = self.controller.parse_filter()
        assert result.sort[0] == "endedAt"
        assert result.sort[1] == "desc"

    def test_without_data_started_at_is_one_week_before_current_time(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 8))
        result = self.controller.parse_filter()
        assert result.startedAt == datetime(2000, 1, 1)

    def test_without_data_ended_at_is_current_time(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 8))
        result = self.controller.parse_filter()
        assert result.endedAt == datetime(2000, 1, 8)

    def test_without_data_there_is_no_name_filter(self) -> None:
        result = self.controller.parse_filter()
        assert result.name is None

    def test_without_data_there_is_no_method_filter(self) -> None:
        result = self.controller.parse_filter()
        assert result.method is None

    def test_without_data_there_is_no_args_filter(self) -> None:
        result = self.controller.parse_filter()
        assert result.args is None

    def test_without_data_there_is_no_kwargs_filter(self) -> None:
        result = self.controller.parse_filter()
        assert result.kwargs is None


class FakeClock:
    def __init__(self) -> None:
        self.frozen_time: Optional[datetime] = None

    def get_epoch(self) -> float:
        if self.frozen_time:
            return self.frozen_time.timestamp()
        return time.time()

    def freeze_time(self, timestamp: datetime) -> None:
        self.frozen_time = timestamp

    def unfreeze_time(self) -> None:
        self.frozen_time = None
