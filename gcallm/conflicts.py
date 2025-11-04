"""Conflict detection and parsing for interactive mode."""

import re
from dataclasses import dataclass


@dataclass
class ConflictReport:
    """Parsed conflict information from Claude's response."""

    has_conflicts: bool
    is_important: bool
    needs_user_decision: bool
    phase1_response: str

    @classmethod
    def from_response(cls, response: str) -> "ConflictReport":
        """Parse conflict information from Claude's Phase 1 response.

        Args:
            response: Claude's response text from Phase 1

        Returns:
            ConflictReport with parsed information
        """
        # Check for the special marker indicating we need user input
        needs_user_decision = "<<AWAIT_USER_DECISION>>" in response

        # Check for conflict indicators
        has_important_conflicts = (
            "IMPORTANT CONFLICTS DETECTED" in response or needs_user_decision
        )
        has_minor_conflicts = "MINOR CONFLICTS" in response

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
