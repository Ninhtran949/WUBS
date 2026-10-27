"""The default command shows usage without starting an experiment."""

import pytest

from web_stress_lab.interfaces.cli import main

pytestmark = pytest.mark.unit


def test_no_arguments_show_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    output = capsys.readouterr()
    assert "usage: stresslab" in output.out
    assert output.err == ""
