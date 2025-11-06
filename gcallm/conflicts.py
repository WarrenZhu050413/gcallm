"""Conflict detection and parsing for interactive mode."""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class ConflictReport:
    """Parsed conflict information from Claude's response."""

    has_conflicts: bool
    is_important: bool
    needs_user_decision: bool
    phase1_response: str

    @classmethod
    def from_response(cls, response: str, strict: bool = False) -> "ConflictReport":
        """Parse conflict information from Claude's Phase 1 response.

        Supports both XML format and legacy text format.

        Args:
            response: Claude's response text from Phase 1
            strict: If True, only accept XML format and raise ValueError for text format

        Returns:
            ConflictReport with parsed information

        Raises:
            ValueError: If strict=True and response is not valid XML format
        """
        # Try to extract XML from response (may be embedded in text)
        if "<conflict_analysis>" in response:
            # Extract just the XML portion if there's extra text
            start = response.find("<conflict_analysis>")
            end = response.find("</conflict_analysis>")
            if start != -1 and end != -1:
                xml_content = response[start : end + len("</conflict_analysis>")]
                return cls._from_xml(xml_content)

        # In strict mode, reject non-XML responses
        if strict:
            raise ValueError(
                "Response must be valid XML format. "
                "Expected <conflict_analysis> tag but got text format."
            )

        # Fall back to legacy text parsing
        return cls._from_text(response)

    @classmethod
    def _from_xml(cls, response: str) -> "ConflictReport":
        """Parse XML-formatted conflict report.

        Args:
            response: XML response string

        Returns:
            ConflictReport with parsed information
        """
        try:
            root = ET.fromstring(response.strip())

            # Extract status
            status_elem = root.find("status")
            status = status_elem.text if status_elem is not None else "unknown"

            # Extract user_decision_required
            decision_elem = root.find("user_decision_required")
            needs_user_decision = (
                decision_elem is not None and decision_elem.text == "true"
            )

            # Determine conflict type
            if status == "important_conflicts":
                return cls(
                    has_conflicts=True,
                    is_important=True,
                    needs_user_decision=needs_user_decision,
                    phase1_response=response,
                )
            elif status == "minor_conflicts":
                return cls(
                    has_conflicts=True,
                    is_important=False,
                    needs_user_decision=needs_user_decision,
                    phase1_response=response,
                )
            else:  # no_conflicts
                return cls(
                    has_conflicts=False,
                    is_important=False,
                    needs_user_decision=False,
                    phase1_response=response,
                )
        except ET.ParseError:
            # Fall back to text parsing if XML is malformed
            return cls._from_text(response)

    @classmethod
    def _from_text(cls, response: str) -> "ConflictReport":
        """Parse text-formatted conflict report (legacy).

        Args:
            response: Text response string

        Returns:
            ConflictReport with parsed information
        """
        # Check for the special marker indicating we need user input
        needs_user_decision = "<<AWAIT_USER_DECISION>>" in response

        # Check for conflict indicators (flexible matching)
        has_important_conflicts = (
            "IMPORTANT CONFLICT" in response  # Matches both singular and plural
            or needs_user_decision
        )
        has_minor_conflicts = "MINOR CONFLICT" in response  # Matches both forms

        # Determine if we need to stop and ask user
        if has_important_conflicts:
            return cls(
                has_conflicts=True,
                is_important=True,
                needs_user_decision=True,
                phase1_response=response,
            )
        elif has_minor_conflicts:
            return cls(
                has_conflicts=True,
                is_important=False,
                needs_user_decision=False,
                phase1_response=response,
            )
        else:
            # No conflicts or "NO CONFLICTS" marker
            return cls(
                has_conflicts=False,
                is_important=False,
                needs_user_decision=False,
                phase1_response=response,
            )


def extract_proposed_events(response: str) -> list[str]:
    """Extract proposed event titles from Phase 1 response.

    Args:
        response: Claude's Phase 1 response

    Returns:
        List of event titles
    """
    events = []

    # Look for lines starting with "- **" which indicate event details
    lines = response.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        # Look for title lines (first bold item, not labeled fields)
        if line.startswith("- **") and i > 0:
            # Check if previous line suggests this is under "Proposed" section
            prev_context = "\n".join(lines[max(0, i - 5) : i]).lower()
            if "proposed" in prev_context or "will create" in prev_context:
                # Extract title
                match = re.search(r"- \*\*([^*]+)\*\*", line)
                if match and "date" not in match.group(1).lower():
                    title = match.group(1).strip()
                    if title:
                        events.append(title)

    return events


def extract_conflicts(response: str) -> list[str]:
    """Extract conflicting event titles from Phase 1 response.

    Args:
        response: Claude's Phase 1 response

    Returns:
        List of conflicting event descriptions
    """
    conflicts = []

    # Find the "Conflicts detected:" section
    lines = response.split("\n")
    in_conflicts_section = False

    for line in lines:
        line = line.strip()

        if "conflicts detected:" in line.lower():
            in_conflicts_section = True
            continue

        if in_conflicts_section:
            # Stop at empty line or next section
            if not line or line.startswith("<<"):
                break

            # Extract conflict event
            if line.startswith("- **"):
                # Extract the full conflict description
                conflict_text = line[2:].strip()  # Remove "- "
                conflicts.append(conflict_text)

    return conflicts
