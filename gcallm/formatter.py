"""Rich formatting for gcallm output."""

import re
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table


def format_event_response(response: str, console: Console) -> None:
    """Format and display event creation response with Rich.

    Args:
        response: Raw text response from Claude
        console: Rich console for output
    """
    # Parse the response to extract structured information
    lines = response.strip().split("\n")

    # Look for the success indicator
    if "✅" in response or "Created" in response:
        # Extract event details - look for markdown list items
        current_event = {}
        events = []

        for line in lines:
            line = line.strip()

            # Skip empty lines, explanatory text
            if not line or line.startswith("I'll") or line.startswith("Now I'll"):
                continue

            # Look for lines starting with "- **"
            if line.startswith("- **"):
                # This could be title, date, description, or link
                content = line[2:].strip()  # Remove "- "

                # Check if it's a labeled field (e.g., "Date & Time:")
                if "Date & Time:" in content or "**Date & Time:**" in content:
                    datetime_text = re.sub(
                        r"\*\*Date & Time:\*\*|\*\*", "", content
                    ).strip()
                    current_event["datetime"] = datetime_text
                elif "Description:" in content:
                    desc_text = re.sub(
                        r"\*\*Description:\*\*|\*\*", "", content
                    ).strip()
                    current_event["description"] = desc_text
                elif "Event Link:" in content or "Link:" in content:
                    # Extract URL
                    url_match = re.search(
                        r"https://www\.google\.com/calendar[^\s\)]*", content
                    )
                    if url_match:
                        current_event["link"] = url_match.group(0)
                elif "Every day" in content or "at" in content:
                    # This is datetime information without label
                    datetime_text = re.sub(r"\*\*", "", content).strip()
                    current_event["datetime"] = datetime_text
                else:
                    # This is likely the title (first bold item without a label)
                    title_text = re.sub(r"\*\*", "", content).strip()
                    if title_text and not current_event.get("title"):
                        current_event["title"] = title_text

            # Also check for standalone URLs
            elif "https://www.google.com/calendar" in line:
                url_match = re.search(
                    r"https://www\.google\.com/calendar[^\s\)]*", line
                )
                if url_match:
                    current_event["link"] = url_match.group(0)

        # Add the event if we have data
        if current_event:
            events.append(current_event)

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
                if "datetime" in event:
                    table.add_row("When:", event["datetime"])

                # Add description if present
                if "description" in event:
                    table.add_row("Details:", event["description"])

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

            # Check for conflicts or notes
            if "⚠️" in response or "Note:" in response or "conflict" in response.lower():
                # Extract warning/note text
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
