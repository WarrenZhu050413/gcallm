"""Rich formatting for gcallm output."""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from gcallm.conflicts import ConflictReport


def parse_xml_events(response: str) -> list[dict[str, str]]:
    """Parse XML-formatted event data from Claude's response.

    Args:
        response: Text response from Claude containing XML <events> block

    Returns:
        List of event dictionaries with 'title', 'when', and 'link' keys
    """
    events = []

    try:
        # Extract XML block from response
        match = re.search(r'<events>.*?</events>', response, re.DOTALL)
        if not match:
            return []

        xml_str = match.group(0)

        # Fix common XML issues: unescaped & in URLs
        # Replace & with &amp; but only in <link> tags to avoid breaking other content
        xml_str = re.sub(
            r'(<link>)(.*?)(</link>)',
            lambda m: m.group(1) + m.group(2).replace('&', '&amp;') + m.group(3),
            xml_str,
            flags=re.DOTALL
        )

        root = ET.fromstring(xml_str)

        for event_elem in root.findall('event'):
            event = {}

            title_elem = event_elem.find('title')
            if title_elem is not None and title_elem.text:
                event['title'] = title_elem.text.strip()

            when_elem = event_elem.find('when')
            if when_elem is not None and when_elem.text:
                event['when'] = when_elem.text.strip()

            link_elem = event_elem.find('link')
            if link_elem is not None and link_elem.text:
                event['link'] = link_elem.text.strip()

            # Only add event if it has at least a title
            if 'title' in event:
                events.append(event)

    except ET.ParseError:
        # If XML parsing fails, return empty list
        pass

    return events


def format_iso_datetime(iso_string: str) -> str:
    """Format ISO 8601 datetime to human-readable string.

    Args:
        iso_string: ISO 8601 datetime string (e.g., "2025-11-05T09:00:00-05:00")

    Returns:
        Human-readable datetime (e.g., "November 5, 2025 at 9:00 AM - 9:30 AM (EST)")
    """
    try:
        dt = datetime.fromisoformat(iso_string)
        # Format: "November 5, 2025 at 9:00 AM"
        return dt.strftime("%B %d, %Y at %-I:%M %p")
    except (ValueError, AttributeError):
        # Fallback to original string if parsing fails
        return iso_string


def format_tool_results(tool_results: list[dict], console: Console) -> None:
    """Format and display MCP tool results directly.

    Args:
        tool_results: List of event dicts from MCP tool
        console: Rich console for output
    """
    if not tool_results:
        return

    for event in tool_results:
        # Create a table for event details
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="cyan bold", width=12)
        table.add_column(style="white")

        # Add title
        if "summary" in event:
            table.add_row("Event:", f"[bold green]{event['summary']}[/bold green]")

        # Add date/time
        if "start" in event and "end" in event:
            start_formatted = format_iso_datetime(event["start"])
            end_dt = datetime.fromisoformat(event["end"])
            end_time = end_dt.strftime("%-I:%M %p")
            # Extract timezone from start
            try:
                tz = datetime.fromisoformat(event["start"]).strftime("%Z")
                if not tz:  # If no timezone name, try to extract from offset
                    tz = "EST"  # Default fallback
            except (ValueError, KeyError):
                tz = "EST"

            datetime_str = f"{start_formatted} - {end_time} ({tz})"
            table.add_row("When:", datetime_str)

        # Add location if present
        if "location" in event and event["location"]:
            table.add_row("Location:", event["location"])

        # Add link
        if "htmlLink" in event:
            table.add_row(
                "Link:", f"[link={event['htmlLink']}]{event['htmlLink']}[/link]"
            )

        # Display in a panel
        console.print()
        console.print(
            Panel(
                table,
                title="[bold green]✅ Event Created Successfully[/bold green]",
                border_style="green",
            )
        )
        console.print()


def format_event_response(response: str, console: Console) -> None:
    """Format and display event creation response with Rich.

    Args:
        response: Raw text response from Claude
        console: Rich console for output
    """
    # Parse XML events from response
    events = parse_xml_events(response)

    # Display events in a nice format
    if events:
        for event in events:
            # Create a table for event details
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column(style="cyan bold", width=12)
            table.add_column(style="white")

            # Add title
            if "title" in event:
                table.add_row(
                    "Event:", f"[bold green]{event['title']}[/bold green]"
                )

            # Add date/time
            if "when" in event:
                table.add_row("When:", event["when"])

            # Add link
            if "link" in event:
                # Display full URL (clickable)
                table.add_row(
                    "Link:", f"[link={event['link']}]{event['link']}[/link]"
                )

            # Display in a panel
            console.print()
            console.print(
                Panel(
                    table,
                    title="[bold green]✅ Event Created Successfully[/bold green]",
                    border_style="green",
                )
            )
            console.print()

        # Check for conflicts or notes (outside event loop)
        if (
            "⚠️" in response
            or "Note:" in response
            or "conflict" in response.lower()
        ):
            # Extract warning/note text
            lines = response.strip().split("\n")
            warning_lines = []
            capture = False
            for line in lines:
                if "⚠️" in line or "Note:" in line:
                    capture = True
                if capture:
                    clean_line = (
                        line.strip()
                        .replace("⚠️", "")
                        .replace("**Note:**", "")
                        .strip()
                    )
                    if clean_line and not clean_line.startswith("✅"):
                        warning_lines.append(clean_line)

            if warning_lines:
                warning_text = "\n".join(
                    warning_lines[:5]
                )  # Limit to first 5 lines
                console.print(
                    Panel(
                        warning_text,
                        title="[yellow]⚠️  Note[/yellow]",
                        border_style="yellow",
                    )
                )
                console.print()

        return

    # If we couldn't parse structured output, display as markdown
    md = Markdown(response)
    console.print()
    console.print(md)
    console.print()


def format_error(error_msg: str, console: Optional[Console] = None) -> None:
    """Format and display error message.

    Args:
        error_msg: Error message to display
        console: Rich console for output
    """
    console = console or Console()
    console.print()
    console.print(Panel(f"[red]{error_msg}[/red]", title="❌ Error", border_style="red"))
    console.print()


def format_no_input_warning(console: Optional[Console] = None) -> None:
    """Display warning when no input provided.

    Args:
        console: Rich console for output
    """
    console = console or Console()
    console.print()
    console.print("[yellow]⚠️  No input provided[/yellow]")
    console.print()
    console.print("Usage:")
    console.print('  [cyan]gcallm "Meeting tomorrow at 3pm"[/cyan]  # Direct input')
    console.print("  [cyan]gcallm --clipboard[/cyan]                  # From clipboard")
    console.print("  [cyan]pbpaste | gcallm[/cyan]                    # From stdin")
    console.print("  [cyan]gcallm[/cyan]                              # Open editor")
    console.print()


def display_conflict_report(report: ConflictReport, console: Console) -> None:
    """Display a nicely formatted conflict report to the user.

    Args:
        report: Parsed conflict report
        console: Rich console for output
    """
    # Display the full response as markdown in a panel
    md = Markdown(report.phase1_response)

    if report.is_important:
        console.print()
        console.print(
            Panel(
                md,
                title="[yellow]⚠️  Scheduling Conflicts Detected[/yellow]",
                border_style="yellow",
            )
        )
    else:
        console.print()
        console.print(
            Panel(
                md,
                title="[cyan]📋 Event Analysis[/cyan]",
                border_style="cyan",
            )
        )


def format_success_message(message: str, console: Optional[Console] = None) -> None:
    """Format and display success message.

    Args:
        message: Success message
        console: Rich console for output
    """
    console = console or Console()
    console.print()
    console.print(
        Panel(f"[green]{message}[/green]", title="✅ Success", border_style="green")
    )
    console.print()
