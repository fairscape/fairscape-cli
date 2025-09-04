from fairscape_cli.__main__ import cli as fairscape_cli_app

def test_cli_invoked_without_command(runner):
    result = runner.invoke(fairscape_cli_app)
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output
    assert "rocrate" in result.output
    assert "import" in result.output
    assert "publish" in result.output
    assert "schema" in result.output
    assert "build" in result.output

def test_cli_invoked_with_help_flag(runner):
    result = runner.invoke(fairscape_cli_app, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output
    assert "FAIRSCAPE CLI" in result.output