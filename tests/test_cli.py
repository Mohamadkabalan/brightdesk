from brightdesk.cli import main  # The function behind the `brightdesk` command
from brightdesk.config import Settings  # Build settings by hand: no dependence on .env


def test_info_masks_the_api_key(capsys):  # pytest passes the capsys fixture in
    key = "sk-ant-test-0000000000001234"  # A fake key for the test
    settings = Settings(_env_file=None, anthropic_api_key=key)  # _env_file=None: skip .env
    assert main(["info"], settings=settings) == 0  # Run `brightdesk info`, expect success
    output = capsys.readouterr().out  # Everything the command printed
    assert "set (…1234)" in output  # The masked form is shown...
    assert key not in output  # ...and the real key never is
