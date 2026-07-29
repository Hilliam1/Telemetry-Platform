from types import SimpleNamespace

import pytest

from app.ingest import Collector


class FakeConnection:
    def commit(self):
        raise RuntimeError("commit failed")


class FakeState:
    def __init__(self):
        self.updated = []
        self.saved = False

    def get_last_record_id(self, source_type, channel):
        return 0

    def update_record_id(self, source_type, channel, record_id):
        self.updated.append((source_type, channel, record_id))

    def save(self):
        self.saved = True


class FakeReader:
    def __init__(self, event_xml_documents):
        self.event_xml_documents = event_xml_documents

    def read_channel(self, channel, last_record_id):
        return self.event_xml_documents


class FakeParser:
    def parse(self, event_xml):
        return event_xml


def test_state_does_not_advance_when_database_commit_fails(monkeypatch):
    collector = Collector.__new__(Collector)
    collector.hostname = "test-host"
    collector.settings = SimpleNamespace(batch_size=10)
    collector.conn = FakeConnection()
    collector.state = FakeState()

    parsed_events = [
        {
            "computer": "test-host",
            "provider": "provider",
            "event_id": 1,
            "record_id": 101,
            "severity": "Information",
            "time_created": "2026-07-27T00:00:00+00:00",
            "message": "event one",
            "raw": {},
        },
        {
            "computer": "test-host",
            "provider": "provider",
            "event_id": 1,
            "record_id": 102,
            "severity": "Information",
            "time_created": "2026-07-27T00:00:01+00:00",
            "message": "event two",
            "raw": {},
        },
    ]

    collector.reader = FakeReader(parsed_events)
    collector.parser = FakeParser()

    monkeypatch.setattr(collector, "_insert_event", lambda **kwargs: None)
    monkeypatch.setattr(collector, "_insert_process_event", lambda event: None)

    with pytest.raises(RuntimeError, match="commit failed"):
        collector._ingest_channel("sysmon", "channel")

    assert collector.state.updated == []
    assert collector.state.saved is False

