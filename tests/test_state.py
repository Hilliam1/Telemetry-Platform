import json

import pytest

from app.state import CollectorState


def test_missing_state_file_starts_empty(tmp_path):
    state_file = tmp_path / "collector_state.json"

    state = CollectorState(state_file)

    assert state.as_dict() == {}
    assert state.get_last_record_id("sysmon", "channel") == 0


def test_state_update_and_reload(tmp_path):
    state_file = tmp_path / "collector_state.json"

    state = CollectorState(state_file)
    state.update_record_id(
        "sysmon",
        "Microsoft-Windows-Sysmon/Operational",
        42,
    )
    state.save()

    reloaded = CollectorState(state_file)

    assert (
        reloaded.get_last_record_id(
            "sysmon",
            "Microsoft-Windows-Sysmon/Operational",
        )
        == 42
    )


def test_record_id_cannot_move_backward(tmp_path):
    state_file = tmp_path / "collector_state.json"

    state = CollectorState(state_file)
    state.update_record_id("sysmon", "channel", 100)
    state.update_record_id("sysmon", "channel", 50)

    assert state.get_last_record_id("sysmon", "channel") == 100


def test_equal_record_id_is_allowed(tmp_path):
    state_file = tmp_path / "collector_state.json"

    state = CollectorState(state_file)
    state.update_record_id("sysmon", "channel", 100)
    state.update_record_id("sysmon", "channel", 100)

    assert state.get_last_record_id("sysmon", "channel") == 100


def test_negative_record_id_is_rejected(tmp_path):
    state_file = tmp_path / "collector_state.json"
    state = CollectorState(state_file)

    with pytest.raises(ValueError):
        state.update_record_id("sysmon", "channel", -1)


def test_invalid_json_starts_empty(tmp_path):
    state_file = tmp_path / "collector_state.json"
    state_file.write_text(
        "{broken-json",
        encoding="utf-8",
    )

    state = CollectorState(state_file)

    assert state.as_dict() == {}


def test_non_object_json_starts_empty(tmp_path):
    state_file = tmp_path / "collector_state.json"
    state_file.write_text(
        json.dumps(["unexpected", "list"]),
        encoding="utf-8",
    )

    state = CollectorState(state_file)

    assert state.as_dict() == {}


def test_invalid_values_are_ignored(tmp_path):
    state_file = tmp_path / "collector_state.json"

    state_file.write_text(
        json.dumps(
            {
                "sysmon:channel": 50,
                "system:channel": "invalid",
                "security:channel": -25,
            }
        ),
        encoding="utf-8",
    )

    state = CollectorState(state_file)

    assert state.get_last_record_id("sysmon", "channel") == 50
    assert state.get_last_record_id("system", "channel") == 0
    assert state.get_last_record_id("security", "channel") == 0


def test_save_creates_parent_directory(tmp_path):
    state_file = (
        tmp_path
        / "runtime"
        / "state"
        / "collector_state.json"
    )

    state = CollectorState(state_file)
    state.update_record_id("sysmon", "channel", 25)
    state.save()

    assert state_file.exists()


def test_save_does_not_leave_temporary_file(tmp_path):
    state_file = tmp_path / "collector_state.json"

    state = CollectorState(state_file)
    state.update_record_id("sysmon", "channel", 25)
    state.save()

    temporary_file = state_file.with_name(
        f"{state_file.name}.tmp"
    )

    assert not temporary_file.exists()