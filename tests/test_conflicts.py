"""Tests for conflict detection and parsing."""

from gcallm.conflicts import (
    ConflictReport,
    extract_proposed_events,
    extract_conflicts,
)


class TestXMLConflictParsing:
    """Test XML-based conflict report parsing."""

    def test_parse_xml_important_conflict(self):
        """Test parsing XML response with important conflicts."""
        response = """<conflict_analysis>
  <status>important_conflicts</status>
  <proposed_events>
    <event>
      <title>Meeting with Jack</title>
      <datetime>Friday, November 7, 2025 at 2:00 AM - 3:00 AM (EST)</datetime>
    </event>
  </proposed_events>
  <conflicts>
    <conflict>
      <title>Existing Event</title>
      <time>2:00 AM - 3:00 AM</time>
    </conflict>
  </conflicts>
  <user_decision_required>true</user_decision_required>
</conflict_analysis>"""

        report = ConflictReport.from_response(response)

        assert report.has_conflicts is True
        assert report.is_important is True
        assert report.needs_user_decision is True

    def test_parse_xml_no_conflicts(self):
        """Test parsing XML response with no conflicts."""
        response = """<conflict_analysis>
  <status>no_conflicts</status>
  <proposed_events>
    <event>
      <title>Lunch Meeting</title>
      <datetime>Monday at 12:00 PM - 1:00 PM</datetime>
    </event>
  </proposed_events>
  <user_decision_required>false</user_decision_required>
</conflict_analysis>"""

        report = ConflictReport.from_response(response)

        assert report.has_conflicts is False
        assert report.is_important is False
        assert report.needs_user_decision is False

    def test_parse_xml_minor_conflicts(self):
        """Test parsing XML response with minor conflicts."""
        response = """<conflict_analysis>
  <status>minor_conflicts</status>
  <proposed_events>
    <event>
      <title>Coffee Chat</title>
      <datetime>Friday at 10:00 AM - 10:30 AM</datetime>
    </event>
  </proposed_events>
  <conflicts>
    <conflict>
      <title>Team Standup</title>
      <time>10:00 AM - 10:15 AM</time>
    </conflict>
  </conflicts>
  <user_decision_required>false</user_decision_required>
</conflict_analysis>"""

        report = ConflictReport.from_response(response)

        assert report.has_conflicts is True
        assert report.is_important is False
        assert report.needs_user_decision is False


class TestConflictReport:
    """Test ConflictReport parsing."""

    def test_parse_important_conflicts(self):
        """Test parsing response with important conflicts."""
        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

Proposed event(s):
- **Team Meeting**
- **Date & Time:** Tomorrow at 2:00 PM - 3:00 PM

Conflicts detected:
- **Project Review** (2:00 PM - 2:30 PM)
- **Client Call** (2:30 PM - 3:00 PM)

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)

        assert report.has_conflicts is True
        assert report.is_important is True
        assert report.needs_user_decision is True
        assert "IMPORTANT CONFLICTS" in report.phase1_response

    def test_parse_minor_conflicts(self):
        """Test parsing response with minor conflicts."""
        response = """📋 CONFLICT CHECK: MINOR CONFLICTS

I will create the following event(s):
- **Coffee Chat**
- **Date & Time:** Friday at 10:00 AM - 10:30 AM

Note: Minor conflict with "Team Standup" (10:00 AM - 10:15 AM), but proceeding as requested."""

        report = ConflictReport.from_response(response)

        assert report.has_conflicts is True
        assert report.is_important is False
        assert report.needs_user_decision is False

    def test_parse_no_conflicts(self):
        """Test parsing response with no conflicts."""
        response = """📋 CONFLICT CHECK: NO CONFLICTS

I will create the following event(s):
- **Lunch Meeting**
- **Date & Time:** Monday at 12:00 PM - 1:00 PM
- **Location:** Cafe Corner

Ready to proceed."""

        report = ConflictReport.from_response(response)

        assert report.has_conflicts is False
        assert report.is_important is False
        assert report.needs_user_decision is False

    def test_parse_await_marker(self):
        """Test that AWAIT_USER_DECISION marker triggers user decision."""
        response = """Some response with <<AWAIT_USER_DECISION>> marker"""

        report = ConflictReport.from_response(response)

        assert report.needs_user_decision is True


class TestExtractProposedEvents:
    """Test extracting proposed event titles."""

    def test_extract_single_event(self):
        """Test extracting a single proposed event."""
        response = """Proposed event(s):
- **Team Meeting**
- **Date & Time:** Tomorrow at 2:00 PM"""

        events = extract_proposed_events(response)

        assert len(events) == 1
        assert "Team Meeting" in events

    def test_extract_multiple_events(self):
        """Test extracting multiple proposed events."""
        response = """I will create the following event(s):
- **Standup**
- **Date & Time:** Daily at 9:00 AM
- **Sprint Review**
- **Date & Time:** Friday at 3:00 PM"""

        events = extract_proposed_events(response)

        assert len(events) >= 1
        # At least one event should be extracted
        assert any("Standup" in e or "Sprint Review" in e for e in events)

    def test_extract_no_events(self):
        """Test when no events are in the response."""
        response = """This response has no event titles."""

        events = extract_proposed_events(response)

        # Should return empty list
        assert isinstance(events, list)


class TestExtractConflicts:
    """Test extracting conflicting events."""

    def test_extract_single_conflict(self):
        """Test extracting a single conflict."""
        response = """Conflicts detected:
- **Team Standup** (9:00 AM - 9:30 AM)"""

        conflicts = extract_conflicts(response)

        assert len(conflicts) == 1
        assert "Team Standup" in conflicts[0]

    def test_extract_multiple_conflicts(self):
        """Test extracting multiple conflicts."""
        response = """Conflicts detected:
- **Meeting A** (2:00 PM - 3:00 PM)
- **Meeting B** (3:00 PM - 4:00 PM)
- **All-day Event** (all day)"""

        conflicts = extract_conflicts(response)

        assert len(conflicts) == 3
        assert any("Meeting A" in c for c in conflicts)
        assert any("Meeting B" in c for c in conflicts)
        assert any("All-day Event" in c for c in conflicts)

    def test_extract_no_conflicts(self):
        """Test when no conflicts section exists."""
        response = """📋 CONFLICT CHECK: NO CONFLICTS

Ready to proceed."""

        conflicts = extract_conflicts(response)

        assert len(conflicts) == 0


class TestConflictScenarios:
    """Test realistic conflict scenarios."""

    def test_multiple_important_conflicts(self):
        """Test scenario with multiple overlapping events."""
        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

Proposed event(s):
- **Workshop**
- **Date & Time:** Wednesday at 2:00 PM - 5:00 PM

Conflicts detected:
- **Meeting A** (2:00 PM - 3:00 PM)
- **Meeting B** (3:00 PM - 4:00 PM)
- **Meeting C** (4:00 PM - 5:00 PM)

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)
        conflicts = extract_conflicts(response)

        assert report.needs_user_decision is True
        assert len(conflicts) == 3

    def test_allday_event_conflict(self):
        """Test conflict with all-day event."""
        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

Proposed event(s):
- **Team Offsite**
- **Date & Time:** Friday at 10:00 AM - 4:00 PM

Conflicts detected:
- **Company Holiday** (all day)

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)
        conflicts = extract_conflicts(response)

        assert report.is_important is True
        assert len(conflicts) == 1
        assert "all day" in conflicts[0].lower()

    def test_tentative_conflict(self):
        """Test minor conflict with tentative event."""
        response = """📋 CONFLICT CHECK: MINOR CONFLICTS

I will create the following event(s):
- **Lunch**
- **Date & Time:** Tuesday at 12:00 PM - 1:00 PM

Note: Minor conflict with "Optional Team Lunch (Tentative)" (12:00 PM - 1:00 PM), but proceeding as requested."""

        report = ConflictReport.from_response(response)

        assert report.has_conflicts is True
        assert report.is_important is False
        assert report.needs_user_decision is False
