from autogen_mcp import cli


def test_main_prints_stub(capsys):
    assert cli.main() == 0
    out, _ = capsys.readouterr()
    assert "CLI stub" in out
