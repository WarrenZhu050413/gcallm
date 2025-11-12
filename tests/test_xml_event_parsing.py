"""Test XML event parsing for structured display."""

from gcallm.formatter import parse_xml_events


class TestXMLEventParsing:
    """Test parsing XML event responses."""

    def test_parse_single_event(self):
        """Should parse single event from XML."""
        xml_response = """
Here are the events created:

<events>
  <event>
    <title>Crisis of Pax Americana Talk</title>
    <when>Nov 12, 2024 at 4:30 PM - 6:00 PM</when>
    <link>https://www.google.com/calendar/event?eid=abc123</link>
  </event>
</events>
"""
        events = parse_xml_events(xml_response)
        
        assert len(events) == 1
        assert events[0]["title"] == "Crisis of Pax Americana Talk"
        assert events[0]["when"] == "Nov 12, 2024 at 4:30 PM - 6:00 PM"
        assert events[0]["link"] == "https://www.google.com/calendar/event?eid=abc123"

    def test_parse_multiple_events(self):
        """Should parse multiple events from XML."""
        xml_response = """
<events>
  <event>
    <title>Event 1</title>
    <when>Nov 12 at 3:40 PM</when>
    <link>https://calendar.google.com/1</link>
  </event>
  <event>
    <title>Event 2</title>
    <when>Nov 12 at 4:30 PM</when>
    <link>https://calendar.google.com/2</link>
  </event>
</events>
"""
        events = parse_xml_events(xml_response)
        
        assert len(events) == 2
        assert events[0]["title"] == "Event 1"
        assert events[1]["title"] == "Event 2"

    def test_parse_no_xml_returns_empty(self):
        """Should return empty list if no XML found."""
        response = "Some text without XML"
        events = parse_xml_events(response)
        assert events == []

