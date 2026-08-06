from datetime import datetime, timezone
from unittest.mock import Mock

from app.source_handlers import (
    HostMetricsSourceHandler,
    WindowsEventSourceHandler,
)
from app.sources import SourceKind, TelemetrySource


def make_windows_source() -> TelemetrySource:
    return TelemetrySource(
        name="windows_system",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("System",),
    )


def make_parsed_event(record_id: int) -> dict:
    return {
        "computer": "HOST-01",
        "provider": "TestProvider",
        "event_id": 100,
        "record_id": record_id,
        "severity": "Information",
        "time_created": datetime.now(timezone.utc),
        "message": "test event",
        "raw": {
            "event_data": {},
        },
    }


def make_windows_handler(
    *,
    conn,
    repository,
    reader,
    parser,
    state,
    hostname="HOST-01",
    detection_engine=None,
    detection_repository=None,
) -> WindowsEventSourceHandler:
    if detection_engine is None:
        detection_engine = Mock()
        detection_engine.evaluate.return_value = ()

    if detection_repository is None:
        detection_repository = Mock()

    return WindowsEventSourceHandler(
        conn=conn,
        repository=repository,
        detection_engine=detection_engine,
        detection_repository=detection_repository,
        reader=reader,
        parser=parser,
        state=state,
        hostname=hostname,
    )


def test_host_metrics_handler_kind():
    handler = HostMetricsSourceHandler(
        conn=Mock(),
        repository=Mock(),
        metrics_collector=Mock(),
    )

    assert handler.kind is SourceKind.HOST_METRICS


def test_host_metrics_handler_persists_snapshot():
    conn = Mock()
    repository = Mock()
    metrics_collector = Mock()

    metrics = {
        "psutil_available": True,
        "host": "HOST-01",
        "cpu_percent": 10.0,
        "memory_percent": 50.0,
        "disk_percent": 60.0,
        "boot_time": datetime.now(timezone.utc),
    }

    metrics_collector.collect.return_value = metrics

    handler = HostMetricsSourceHandler(
        conn=conn,
        repository=repository,
        metrics_collector=metrics_collector,
    )

    result = handler.ingest(
        TelemetrySource(
            name="health_metrics",
            kind=SourceKind.HOST_METRICS,
        )
    )

    assert result == 1
    repository.insert_host_metrics.assert_called_once_with(metrics)
    conn.commit.assert_called_once_with()


def test_host_metrics_handler_skips_without_psutil():
    conn = Mock()
    repository = Mock()
    metrics_collector = Mock()

    metrics_collector.collect.return_value = {
        "psutil_available": False,
    }

    handler = HostMetricsSourceHandler(
        conn=conn,
        repository=repository,
        metrics_collector=metrics_collector,
    )

    result = handler.ingest(
        TelemetrySource(
            name="health_metrics",
            kind=SourceKind.HOST_METRICS,
        )
    )

    assert result == 0
    repository.insert_host_metrics.assert_not_called()
    conn.commit.assert_not_called()


def test_windows_handler_kind():
    handler = make_windows_handler(
        conn=Mock(),
        repository=Mock(),
        reader=Mock(),
        parser=Mock(),
        state=Mock(),
        hostname="HOST-01",
    )

    assert handler.kind is SourceKind.WINDOWS_EVENT


def test_windows_handler_ingests_channel_and_updates_state():
    conn = Mock()
    repository = Mock()
    reader = Mock()
    parser = Mock()
    state = Mock()

    state.get_last_record_id.return_value = 40
    reader.read_channel.return_value = [
        "<Event>one</Event>",
    ]
    parser.parse.return_value = make_parsed_event(41)

    handler = make_windows_handler(
        conn=conn,
        repository=repository,
        reader=reader,
        parser=parser,
        state=state,
        hostname="HOST-01",
    )

    result = handler.ingest(make_windows_source())

    assert result == 1
    reader.read_channel.assert_called_once_with(
        channel="System",
        last_record_id=40,
    )
    repository.insert_log_event.assert_called_once()
    repository.insert_process_event.assert_called_once()
    conn.commit.assert_called_once_with()
    state.update_record_id.assert_called_once_with(
        "windows_system",
        "System",
        41,
    )
    state.save.assert_called_once_with()


def test_windows_handler_uses_default_hostname_when_event_computer_missing():
    conn = Mock()
    repository = Mock()
    reader = Mock()
    parser = Mock()
    state = Mock()

    event = make_parsed_event(41)
    event["computer"] = ""

    state.get_last_record_id.return_value = 40
    reader.read_channel.return_value = [
        "<Event>one</Event>",
    ]
    parser.parse.return_value = event

    handler = make_windows_handler(
        conn=conn,
        repository=repository,
        reader=reader,
        parser=parser,
        state=state,
        hostname="FALLBACK-HOST",
    )

    handler.ingest(make_windows_source())

    assert repository.insert_log_event.call_args.kwargs["source_host"] == (
        "FALLBACK-HOST"
    )


def test_windows_handler_sorts_events_before_checkpoint_update():
    conn = Mock()
    repository = Mock()
    reader = Mock()
    parser = Mock()
    state = Mock()

    first_event = make_parsed_event(102)
    second_event = make_parsed_event(101)

    state.get_last_record_id.return_value = 100
    reader.read_channel.return_value = [
        "event-102",
        "event-101",
    ]
    parser.parse.side_effect = [
        first_event,
        second_event,
    ]

    handler = make_windows_handler(
        conn=conn,
        repository=repository,
        reader=reader,
        parser=parser,
        state=state,
        hostname="HOST-01",
    )

    result = handler.ingest(make_windows_source())

    assert result == 2
    assert repository.insert_log_event.call_args_list[0].kwargs[
        "event_record_id"
    ] == 101
    assert repository.insert_log_event.call_args_list[1].kwargs[
        "event_record_id"
    ] == 102
    state.update_record_id.assert_called_once_with(
        "windows_system",
        "System",
        102,
    )


def test_windows_handler_rolls_back_failed_channel():
    conn = Mock()
    reader = Mock()

    reader.read_channel.side_effect = RuntimeError("channel failed")

    handler = make_windows_handler(
        conn=conn,
        repository=Mock(),
        reader=reader,
        parser=Mock(),
        state=Mock(),
        hostname="HOST-01",
    )

    result = handler.ingest(make_windows_source())

    assert result == 0
    conn.rollback.assert_called_once_with()


def test_state_does_not_advance_when_database_commit_fails():
    conn = Mock()
    repository = Mock()
    reader = Mock()
    parser = Mock()
    state = Mock()

    conn.commit.side_effect = RuntimeError("commit failed")
    state.get_last_record_id.return_value = 100
    reader.read_channel.return_value = [
        "event-101",
        "event-102",
    ]
    parser.parse.side_effect = [
        make_parsed_event(101),
        make_parsed_event(102),
    ]

    handler = make_windows_handler(
        conn=conn,
        repository=repository,
        reader=reader,
        parser=parser,
        state=state,
        hostname="HOST-01",
    )

    result = handler.ingest(make_windows_source())

    assert result == 0
    conn.rollback.assert_called_once_with()
    state.update_record_id.assert_not_called()
    state.save.assert_not_called()


def test_windows_handler_persists_detection_findings():
    conn = Mock()
    repository = Mock()
    detection_engine = Mock()
    detection_repository = Mock()
    reader = Mock()
    parser = Mock()
    state = Mock()

    state.get_last_record_id.return_value = 40
    reader.read_channel.return_value = [
        "<Event>one</Event>",
    ]
    event = make_parsed_event(41)
    finding = Mock()

    parser.parse.return_value = event
    detection_engine.evaluate.return_value = (finding,)

    handler = make_windows_handler(
        conn=conn,
        repository=repository,
        detection_engine=detection_engine,
        detection_repository=detection_repository,
        reader=reader,
        parser=parser,
        state=state,
        hostname="HOST-01",
    )

    source = TelemetrySource(
        name="sysmon",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Microsoft-Windows-Sysmon/Operational",),
    )

    result = handler.ingest(source)

    assert result == 1
    detection_engine.evaluate.assert_called_once_with(event)
    detection_repository.insert_findings.assert_called_once_with((finding,))
    conn.commit.assert_called_once_with()
    state.update_record_id.assert_called_once()


def test_detection_persistence_failure_rolls_back_and_keeps_checkpoint():
    conn = Mock()
    repository = Mock()
    detection_engine = Mock()
    detection_repository = Mock()
    reader = Mock()
    parser = Mock()
    state = Mock()

    state.get_last_record_id.return_value = 40
    reader.read_channel.return_value = [
        "<Event>one</Event>",
    ]
    parser.parse.return_value = make_parsed_event(41)

    detection_engine.evaluate.return_value = (Mock(),)
    detection_repository.insert_findings.side_effect = RuntimeError(
        "finding insert failed"
    )

    handler = make_windows_handler(
        conn=conn,
        repository=repository,
        detection_engine=detection_engine,
        detection_repository=detection_repository,
        reader=reader,
        parser=parser,
        state=state,
        hostname="HOST-01",
    )

    source = TelemetrySource(
        name="sysmon",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Sysmon",),
    )

    assert handler.ingest(source) == 0

    conn.rollback.assert_called_once_with()
    conn.commit.assert_not_called()
    state.update_record_id.assert_not_called()
    state.save.assert_not_called()
