from datetime import datetime, timezone
import xml.etree.ElementTree as ET

import pytest

from app.parsers.windows_event_parser import WindowsEventParser


def test_parse_complete_windows_event():
    xml = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <Provider Name="Microsoft-Windows-Test" />
        <EventID>1001</EventID>
        <Level>3</Level>
        <TimeCreated SystemTime="2026-07-29T16:00:00.0000000Z" />
        <EventRecordID>42</EventRecordID>
        <Computer>HOST-01</Computer>
      </System>
      <EventData>
        <Data Name="Image">C:\\Windows\\test.exe</Data>
        <Data Name="User">DOMAIN\\user</Data>
      </EventData>
    </Event>
    """

    parser = WindowsEventParser(
        default_computer="DEFAULT-HOST"
    )

    event = parser.parse(xml)

    assert event["provider"] == "Microsoft-Windows-Test"
    assert event["event_id"] == 1001
    assert event["record_id"] == 42
    assert event["severity"] == "Warning"
    assert event["computer"] == "HOST-01"
    assert event["message"] == (
        "Image=C:\\Windows\\test.exe User=DOMAIN\\user"
    )
    assert event["time_created"] == datetime(
        2026,
        7,
        29,
        16,
        0,
        tzinfo=timezone.utc,
    )
    assert event["raw"]["event_data"]["Image"] == (
        "C:\\Windows\\test.exe"
    )


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("0", "LogAlways"),
        ("1", "Critical"),
        ("2", "Error"),
        ("3", "Warning"),
        ("4", "Information"),
        ("5", "Verbose"),
        ("99", "99"),
    ],
)
def test_maps_windows_severity_levels(level, expected):
    xml = f"""
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <EventID>1</EventID>
        <Level>{level}</Level>
        <EventRecordID>10</EventRecordID>
      </System>
    </Event>
    """

    parser = WindowsEventParser(default_computer="HOST")

    assert parser.parse(xml)["severity"] == expected


def test_uses_default_computer_when_computer_is_missing():
    xml = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <EventID>1</EventID>
        <EventRecordID>10</EventRecordID>
      </System>
    </Event>
    """

    parser = WindowsEventParser(default_computer="DEFAULT-HOST")

    event = parser.parse(xml)

    assert event["computer"] == "DEFAULT-HOST"
    assert event["raw"]["computer"] == "DEFAULT-HOST"


def test_unnamed_event_data_uses_indexed_names():
    xml = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <EventID>1</EventID>
        <EventRecordID>10</EventRecordID>
      </System>
      <EventData>
        <Data>alpha</Data>
        <Data>bravo</Data>
      </EventData>
    </Event>
    """

    parser = WindowsEventParser(default_computer="HOST")

    event = parser.parse(xml)

    assert event["raw"]["event_data"] == {
        "Data0": "alpha",
        "Data1": "bravo",
    }
    assert event["message"] == "Data0=alpha Data1=bravo"


def test_nested_user_data_is_preserved():
    xml = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <EventID>1</EventID>
        <EventRecordID>10</EventRecordID>
      </System>
      <UserData>
        <EventXML>
          <SubjectUserName>alice</SubjectUserName>
          <Nested>
            <Value>kept</Value>
          </Nested>
        </EventXML>
      </UserData>
    </Event>
    """

    parser = WindowsEventParser(default_computer="HOST")

    event = parser.parse(xml)

    assert event["raw"]["user_data"] == {
        "EventXML": {
            "SubjectUserName": "alice",
            "Nested": {
                "Value": "kept",
            },
        },
    }
    assert event["message"] == (
        "EventXML={'SubjectUserName': 'alice', "
        "'Nested': {'Value': 'kept'}}"
    )


def test_missing_event_data_user_data_and_provider_are_defaults():
    xml = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <EventID>1</EventID>
        <EventRecordID>10</EventRecordID>
      </System>
    </Event>
    """

    parser = WindowsEventParser(default_computer="HOST")

    event = parser.parse(xml)

    assert event["provider"] == ""
    assert event["message"] == ""
    assert event["raw"]["event_data"] == {}
    assert event["raw"]["user_data"] == {}


def test_parses_windows_utc_timestamp():
    xml = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <EventID>1</EventID>
        <EventRecordID>10</EventRecordID>
        <TimeCreated SystemTime="2026-07-29T16:30:15Z" />
      </System>
    </Event>
    """

    parser = WindowsEventParser(default_computer="HOST")

    assert parser.parse(xml)["time_created"] == datetime(
        2026,
        7,
        29,
        16,
        30,
        15,
        tzinfo=timezone.utc,
    )


def test_malformed_xml_raises_parse_error():
    parser = WindowsEventParser(default_computer="HOST")

    with pytest.raises(ET.ParseError):
        parser.parse("<Event>")


@pytest.mark.parametrize(
    "field",
    [
        "EventID",
        "EventRecordID",
    ],
)
def test_malformed_numeric_fields_raise_value_error(field):
    xml = f"""
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <EventID>{'bad' if field == 'EventID' else '1'}</EventID>
        <EventRecordID>{'bad' if field == 'EventRecordID' else '10'}</EventRecordID>
      </System>
    </Event>
    """

    parser = WindowsEventParser(default_computer="HOST")

    with pytest.raises(ValueError):
        parser.parse(xml)
