"""Tests for InputContext dataclass."""


from gcallm.helpers.input import InputContext


class TestInputContext:
    """Test InputContext dataclass."""

    def test_empty_context_has_no_input(self):
        """Empty InputContext should report no input."""
        context = InputContext()
        assert not context.has_any_input()

    def test_context_with_text_input_has_input(self):
        """InputContext with text_input should report has input."""
        context = InputContext(text_input="Meeting tomorrow")
        assert context.has_any_input()

    def test_context_with_screenshot_paths_has_input(self):
        """InputContext with screenshot_paths should report has input."""
        context = InputContext(screenshot_paths=["/path/to/screenshot.png"])
        assert context.has_any_input()

    def test_context_with_both_inputs_has_input(self):
        """InputContext with both text and screenshots should report has input."""
        context = InputContext(
            text_input="Coffee chat",
            screenshot_paths=["/path/to/screenshot.png"],
        )
        assert context.has_any_input()

    def test_context_with_empty_text_has_no_input(self):
        """InputContext with empty string should report no input."""
        context = InputContext(text_input="")
        assert not context.has_any_input()

    def test_context_with_empty_screenshot_list_has_no_input(self):
        """InputContext with empty list should report no input."""
        context = InputContext(screenshot_paths=[])
        assert not context.has_any_input()

    def test_context_defaults_to_none(self):
        """InputContext should default both fields to None."""
        context = InputContext()
        assert context.text_input is None
        assert context.screenshot_paths is None
