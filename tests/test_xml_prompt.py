"""Tests for XML-based interactive system prompt."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from gcallm.agent import INTERACTIVE_SYSTEM_PROMPT


class TestXMLInteractivePrompt:
    """Test that interactive prompt uses XML format."""

    def test_prompt_contains_xml_examples(self):
        """Test that prompt contains few-shot XML examples."""
        # Should have example conflict_analysis tags
        assert "<conflict_analysis>" in INTERACTIVE_SYSTEM_PROMPT
        assert "</conflict_analysis>" in INTERACTIVE_SYSTEM_PROMPT

        # Should show all three statuses in examples
        assert "important_conflicts" in INTERACTIVE_SYSTEM_PROMPT
        assert "no_conflicts" in INTERACTIVE_SYSTEM_PROMPT
        assert "minor_conflicts" in INTERACTIVE_SYSTEM_PROMPT

    def test_prompt_has_xml_structure(self):
        """Test that prompt defines XML structure."""
        # Should define XML elements
        assert "<status>" in INTERACTIVE_SYSTEM_PROMPT
        assert "<proposed_events>" in INTERACTIVE_SYSTEM_PROMPT
        assert "<conflicts>" in INTERACTIVE_SYSTEM_PROMPT
        assert "<user_decision_required>" in INTERACTIVE_SYSTEM_PROMPT

    def test_prompt_has_examples_before_instructions(self):
        """Test that examples come before workflow instructions."""
        # Find positions
        examples_pos = INTERACTIVE_SYSTEM_PROMPT.find("<conflict_analysis>")
        workflow_pos = INTERACTIVE_SYSTEM_PROMPT.find("WORKFLOW:")

        # Examples should come first
        assert examples_pos < workflow_pos, "Examples should appear before workflow"

    def test_prompt_has_critical_emphasis(self):
        """Test that prompt emphasizes using exact XML format."""
        # Should have strong language about following format
        assert "CRITICAL" in INTERACTIVE_SYSTEM_PROMPT or "MUST" in INTERACTIVE_SYSTEM_PROMPT
        assert "exact" in INTERACTIVE_SYSTEM_PROMPT.lower() or "exactly" in INTERACTIVE_SYSTEM_PROMPT.lower()
