from unittest.mock import Mock, patch

import pywintypes
import pytest

from app.windows_reader import WindowsEventReader


def make_windows_error(winerror: int) -> pywintypes.error:
    return pywintypes.error(
        winerror,
        "WindowsEventReader",
        "test error",
    )


def test_build_query_without_checkpoint():
    assert WindowsEventReader._build_query(0) == "*"


def test_build_query_with_checkpoint():
    assert (
        WindowsEventReader._build_query(42)
        == "*[System[EventRecordID > 42]]"
    )


def test_rejects_invalid_batch_size():
    with pytest.raises(ValueError):
        WindowsEventReader(batch_size=0)


def test_rejects_negative_record_id():
    reader = WindowsEventReader(batch_size=100)

    with pytest.raises(ValueError):
        reader.read_channel(
            channel="System",
            last_record_id=-1,
        )


@patch("app.windows_reader.win32evtlog.EvtRender")
@patch("app.windows_reader.win32evtlog.EvtNext")
@patch("app.windows_reader.win32evtlog.EvtQuery")
def test_reads_and_renders_events(
    mock_query,
    mock_next,
    mock_render,
):
    query_handle = Mock()
    event_one = Mock()
    event_two = Mock()

    mock_query.return_value = query_handle
    mock_next.side_effect = [
        [event_one, event_two],
        [],
    ]
    mock_render.side_effect = [
        "<Event>one</Event>",
        "<Event>two</Event>",
    ]

    reader = WindowsEventReader(batch_size=100)

    result = reader.read_channel(
        channel="System",
        last_record_id=25,
    )

    assert result == [
        "<Event>one</Event>",
        "<Event>two</Event>",
    ]


@patch("app.windows_reader.win32evtlog.EvtNext")
@patch("app.windows_reader.win32evtlog.EvtQuery")
def test_no_more_items_ends_reading(
    mock_query,
    mock_next,
):
    mock_query.return_value = Mock()
    mock_next.side_effect = make_windows_error(259)

    reader = WindowsEventReader(batch_size=100)

    assert reader.read_channel("System") == []


@patch("app.windows_reader.win32evtlog.EvtNext")
@patch("app.windows_reader.win32evtlog.EvtQuery")
def test_unexpected_windows_error_is_raised(
    mock_query,
    mock_next,
):
    mock_query.return_value = Mock()
    mock_next.side_effect = make_windows_error(5)

    reader = WindowsEventReader(batch_size=100)

    with pytest.raises(pywintypes.error):
        reader.read_channel("Security")


@patch("app.windows_reader.win32evtlog.EvtNext")
@patch("app.windows_reader.win32evtlog.EvtQuery")
def test_batch_limit_is_enforced(
    mock_query,
    mock_next,
):
    mock_query.return_value = Mock()
    mock_next.return_value = list(range(10))

    reader = WindowsEventReader(
        batch_size=10,
        native_batch_size=25,
    )

    handles = reader._read_handles(
        mock_query.return_value
    )

    assert len(handles) == 10
    mock_next.assert_called_once_with(
        mock_query.return_value,
        10,
    )