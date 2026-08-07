from app.source_handlers import WindowsEventSourceHandler
from app.sources import SourceKind, TelemetrySource


class FakeConnection:
    def __init__(self):
        self.rolled_back = False

    def commit(self):
        raise RuntimeError("commit failed")

    def rollback(self):
        self.rolled_back = True


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


class FakeRepository:
    def __init__(self):
        self.log_events = []
        self.process_events = []

    def insert_log_event(self, **kwargs):
        self.log_events.append(kwargs)

    def insert_process_event(self, event):
        self.process_events.append(event)
        return False


class FakeDetectionEngine:
    def evaluate(self, event):
        del event
        return ()


class FakeDetectionRepository:
    def insert_findings(self, findings):
        return len(tuple(findings))


class FakeIntelligenceService:
    def process(self, findings):
        del findings


def test_state_does_not_advance_when_database_commit_fails():
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

    state = FakeState()
    conn = FakeConnection()
    handler = WindowsEventSourceHandler(
        conn=conn,
        repository=FakeRepository(),
        detection_engine=FakeDetectionEngine(),
        detection_repository=FakeDetectionRepository(),
        intelligence_service=FakeIntelligenceService(),
        reader=FakeReader(parsed_events),
        parser=FakeParser(),
        state=state,
        hostname="test-host",
    )

    source = TelemetrySource(
        name="sysmon",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("channel",),
    )

    assert handler.ingest(source) == 0
    assert conn.rolled_back is True
    assert state.updated == []
    assert state.saved is False
