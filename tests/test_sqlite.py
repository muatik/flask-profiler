from typing import Optional
from unittest import TestCase

from flask_profiler.storage.base import FilterQuery, Measurement, RequestMetadata
from flask_profiler.storage.sqlite import Sqlite


class SqliteTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = Sqlite(":memory:", "measurements")

    def tearDown(self) -> None:
        self.db.connection.close()
        super().tearDown()

    def test_dont_get_filter_results_with_empty_db(self) -> None:
        assert not self.db.filter(FilterQuery(limit=10, skip=0, sort=("name", "asc")))

    def test_get_filter_result_when_measurement_is_in_db(self) -> None:
        measurement = self.create_measurement()
        self.db.insert(measurement)
        assert self.db.filter(FilterQuery(limit=10, skip=0, sort=("name", "asc")))

    def test_inserted_measurements_preserve_their_name(self) -> None:
        expected_name = "test 123"
        measurement = self.create_measurement(name=expected_name)
        self.db.insert(measurement)
        measurements = self.db.filter(
            FilterQuery(limit=10, skip=0, sort=("name", "asc"))
        )
        assert measurements[0].name == expected_name

    def test_that_inserted_request_metadata_is_returned_back_as_is(self) -> None:
        expected_request_metadata = RequestMetadata(
            url="testurl",
            args=dict(arg="test"),
            form=dict(form="test"),
            headers=dict(header="test"),
            endpoint_name="testendpoint",
            client_address="5.6.2.1",
        )
        self.db.insert(
            self.create_measurement(request_metadata=expected_request_metadata)
        )
        measurements = self.db.filter(
            FilterQuery(limit=10, skip=0, sort=("name", "asc"))
        )
        assert measurements[0].context == expected_request_metadata

    def create_measurement(
        self, name: str = "name", request_metadata: Optional[RequestMetadata] = None
    ) -> Measurement:
        return Measurement(
            name=name,
            args=[],
            kwargs={},
            method="GET",
            context=request_metadata or self.create_request_metadata(),
            startedAt=1.0,
            endedAt=2.0,
        )

    def create_request_metadata(self) -> RequestMetadata:
        return RequestMetadata(
            url="",
            args=dict(),
            form=dict(),
            headers=dict(),
            endpoint_name="",
            client_address="",
        )
