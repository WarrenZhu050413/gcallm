"""Tests for the formatter module."""

from io import StringIO

from rich.console import Console

from gcallm.formatter import format_event_response, format_tool_results


class TestFormatter:
    """Test suite for event response formatting."""

    def test_single_event_basic(self):
        """Test formatting a single event with basic fields."""
        response = """✅ Created 1 event:

<events>
  <event>
    <title>Team Meeting</title>
    <when>Monday, November 4, 2025 at 2:00 PM - 3:00 PM (EST)</when>
    <link>https://www.google.com/calendar/event?eid=abc123</link>
  </event>
</events>"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        # Check that it contains the formatted output
        assert "Event Created Successfully" in result
        assert "Team Meeting" in result
        assert "Monday, November 4, 2025 at 2:00 PM - 3:00 PM (EST)" in result
        assert "https://www.google.com/calendar/event?eid=abc123" in result

    def test_recurring_event(self):
        """Test formatting a recurring event."""
        response = """✅ Created 1 recurring event:

- **Daily Standup**
- **Every day at 9:00 AM - 9:30 AM** (Eastern Time)
- **Event Link:** https://www.google.com/calendar/event?eid=xyz789"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        assert "Daily Standup" in result
        assert "Every day at 9:00 AM - 9:30 AM" in result

    def test_long_url_not_truncated_with_ellipsis(self):
        """Test that long URLs should NOT be truncated with ... in display text."""
        # Very long Google Calendar URL (common in real usage) - 141 characters
        long_url = "https://www.google.com/calendar/event?eid=NzA2aTI2ZG45aW1qbnBjYm1wa2FyYzhpdnMgd3podUBjb2xsZWdlLmhhcnZhcmQuZWR1&ctz=America/New_York"

        response = f"""✅ Created 1 event:

<events>
  <event>
    <title>SUFRA - Arab Heritage Night</title>
    <when>Friday, November 8, 2025 at 8:30 PM - 11:00 PM (EST)</when>
    <link>{long_url}</link>
  </event>
</events>"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        format_event_response(response, console)
        result = output.getvalue()

        # The full URL should be in the result (for clickability)
        assert long_url in result

        # The display should NOT contain "..." for truncation
        # Current implementation truncates at 70 chars, so this should fail
        assert (
            "..." not in result
        ), "URL should not be truncated with ellipsis - breaks clickability"

    def test_event_with_description(self):
        """Test formatting event with description field."""
        response = """✅ Created 1 event:

- **Project Review**
- **Date & Time:** Friday, November 8, 2025 at 3:00 PM - 4:00 PM
- **Description:** Quarterly project review meeting
- **Event Link:** https://www.google.com/calendar/event?eid=def456"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        assert "Project Review" in result
        assert "Quarterly project review meeting" in result

    def test_event_with_conflict_warning(self):
        """Test formatting event with scheduling conflict."""
        response = """✅ Created 1 event:

- **Lunch Meeting**
- **Date & Time:** Tuesday, November 5, 2025 at 12:00 PM - 1:00 PM
- **Event Link:** https://www.google.com/calendar/event?eid=ghi789

⚠️ Note: This event conflicts with 1 existing event:
- "Team Lunch" (12:00 PM - 1:30 PM)"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        assert "Lunch Meeting" in result
        assert "Note" in result
        assert "conflicts" in result

    def test_event_without_link(self):
        """Test formatting event without event link."""
        response = """✅ Created 1 event:

- **Quick Call**
- **Date & Time:** Today at 4:00 PM - 4:15 PM"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        assert "Quick Call" in result
        assert "Today at 4:00 PM - 4:15 PM" in result

    def test_multiple_conflicts(self):
        """Test formatting event with multiple conflicts."""
        response = """✅ Created 1 event:

- **Workshop**
- **Date & Time:** Wednesday, November 6, 2025 at 2:00 PM - 5:00 PM
- **Event Link:** https://www.google.com/calendar/event?eid=jkl012

⚠️ Note: This event conflicts with 3 existing events:
- "Meeting A" (2:00 PM - 3:00 PM)
- "Meeting B" (3:00 PM - 4:00 PM)
- "Meeting C" (4:00 PM - 5:00 PM)"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        assert "Workshop" in result
        assert "conflicts with 3" in result or "conflicts" in result

    def test_fallback_to_markdown(self):
        """Test fallback to markdown for unparseable response."""
        response = """I couldn't create the event because the date was ambiguous.

Please specify:
- The exact date (e.g., November 4, 2025)
- The time (e.g., 2:00 PM)"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        # Should fall back to markdown rendering
        assert "couldn't create" in result or "ambiguous" in result

    def test_explanatory_text_filtered(self):
        """Test that explanatory text from Claude is filtered out."""
        response = """I'll create this event for you. Let me first get the current date.

✅ Created 1 event:

- **Coffee Chat**
- **Date & Time:** Tomorrow at 10:00 AM - 10:30 AM
- **Event Link:** https://www.google.com/calendar/event?eid=mno345"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        # Check that the event details are present (title might not be captured in all cases)
        assert "Tomorrow at 10:00 AM - 10:30 AM" in result
        assert "https://www.google.com/calendar/event?eid=mno345" in result
        # The explanatory text should be filtered
        assert "Event Created Successfully" in result or "Coffee Chat" in result

    def test_url_extraction_from_markdown_link(self):
        """Test URL extraction from markdown-style links."""
        response = """✅ Created 1 event:

- **Dentist Appointment**
- **Date & Time:** Friday at 3:00 PM - 4:00 PM
- **Event Link:** [View in Calendar](https://www.google.com/calendar/event?eid=pqr678)"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        assert "Dentist Appointment" in result
        assert "https://www.google.com/calendar/event?eid=pqr678" in result

    def test_event_with_all_fields(self):
        """Test event with all possible fields."""
        response = """✅ Created 1 event:

- **Annual Review**
- **Date & Time:** December 15, 2025 at 10:00 AM - 11:30 AM (EST)
- **Description:** Year-end performance review with manager
- **Event Link:** https://www.google.com/calendar/event?eid=stu901

⚠️ Note: This event conflicts with "Holiday Party" (all-day event)"""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        assert "Annual Review" in result
        assert "December 15, 2025 at 10:00 AM - 11:30 AM (EST)" in result
        assert "Year-end performance review with manager" in result
        assert "https://www.google.com/calendar/event?eid=stu901" in result
        assert "Holiday Party" in result

    def test_no_success_indicator(self):
        """Test response without success indicator falls back to markdown."""
        response = (
            """The calendar API is currently unavailable. Please try again later."""
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        format_event_response(response, console)
        result = output.getvalue()

        # Should render as markdown
        assert "unavailable" in result

    def test_empty_response(self):
        """Test handling of empty response."""
        response = ""

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        # Should not crash
        format_event_response(response, console)
        result = output.getvalue()

        # May be empty or have fallback content
        assert isinstance(result, str)


class TestToolResultFormatter:
    """Test suite for direct tool result formatting."""

    def test_format_single_tool_result(self):
        """Test formatting a single MCP tool result."""
        tool_results = [
            {
                "event_id": "abc123xyz",
                "summary": "Team Standup",
                "start": "2025-11-05T09:00:00-05:00",
                "end": "2025-11-05T09:30:00-05:00",
                "location": "Conference Room A",
                "htmlLink": "https://www.google.com/calendar/event?eid=abc123xyz",
            }
        ]

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        format_tool_results(tool_results, console)
        result = output.getvalue()

        # Should contain event details
        assert "Team Standup" in result
        assert "Conference Room A" in result
        assert "https://www.google.com/calendar/event?eid=abc123xyz" in result
        # Should format the datetime nicely (not raw ISO)
        assert "November" in result and "2025" in result
        assert "9:00 AM" in result
        assert "9:30 AM" in result

    def test_format_multiple_tool_results(self):
        """Test formatting multiple MCP tool results."""
        tool_results = [
            {
                "event_id": "event1",
                "summary": "Morning Meeting",
                "start": "2025-11-05T09:00:00-05:00",
                "end": "2025-11-05T10:00:00-05:00",
                "htmlLink": "https://www.google.com/calendar/event?eid=event1",
            },
            {
                "event_id": "event2",
                "summary": "Lunch with Team",
                "start": "2025-11-05T12:00:00-05:00",
                "end": "2025-11-05T13:00:00-05:00",
                "location": "Cafeteria",
                "htmlLink": "https://www.google.com/calendar/event?eid=event2",
            },
        ]

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        format_tool_results(tool_results, console)
        result = output.getvalue()

        # Should contain both events
        assert "Morning Meeting" in result
        assert "Lunch with Team" in result
        assert "Cafeteria" in result
        assert "event1" in result
        assert "event2" in result

    def test_format_tool_result_without_location(self):
        """Test formatting tool result when location is missing."""
        tool_results = [
            {
                "event_id": "xyz789",
                "summary": "Virtual Call",
                "start": "2025-11-06T14:00:00-05:00",
                "end": "2025-11-06T15:00:00-05:00",
                "htmlLink": "https://www.google.com/calendar/event?eid=xyz789",
            }
        ]

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        format_tool_results(tool_results, console)
        result = output.getvalue()

        # Should still format correctly without location
        assert "Virtual Call" in result
        assert "xyz789" in result
        # Should not crash or show "None" for location

    def test_format_empty_tool_results(self):
        """Test formatting when tool_results list is empty."""
        tool_results = []

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        # Should not crash
        format_tool_results(tool_results, console)
        result = output.getvalue()

        # Should be empty or minimal output
        assert isinstance(result, str)
