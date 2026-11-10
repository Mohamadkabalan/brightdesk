"""Brightdesk command-line interface (Chapter 1 version).

In your own repository this file lives at ``src/brightdesk/cli.py`` and is registered in
``pyproject.toml`` so that ``uv run brightdesk ...`` calls :func:`main`::

    [project.scripts]
    brightdesk = "brightdesk.cli:main"
"""

from __future__ import annotations  # Allow modern type hints everywhere (good habit)

import argparse  # The standard library's command-line parser
import json
import platform  # Tells us which Python version is running
import sys  # Gives access to stderr for error messages
from collections.abc import Callable, Sequence  # Abstract types for "a function" / "list-like"
from urllib.parse import urlsplit, urlunsplit  # Split a URL into parts and join it back

from pydantic import SecretStr, ValidationError  # Secret wrapper + the error for bad settings

from brightdesk import __version__  # The package version defined in __init__.py
from brightdesk.config import Settings, get_settings  # Our typed configuration

# Every subcommand handler takes the parsed arguments and the settings and returns an exit code.
Handler = Callable[[argparse.Namespace, Settings], int]


def mask_secret(secret: SecretStr | None) -> str:
    """Describe a secret without revealing it: '(not set)', 'set' or 'set (…abcd)'."""
    if secret is None:  # The variable was never provided
        return "(not set)"
    value = secret.get_secret_value()  # Unwrap it, only to inspect it, never to print it whole
    if not value:  # ANTHROPIC_API_KEY= (empty) in .env counts as not set
        return "(not set)"
    if len(value) < 16:  # Too short to show any of it safely
        return "set"
    return f"set (…{value[-4:]})"  # The last 4 chars help you tell two keys apart


def redact_url(url: str | None) -> str:
    """Hide the password in a URL such as postgresql://user:pass@host/db."""
    if not url:  # None or empty string
        return "(not set)"
    parts = urlsplit(url)  # -> scheme, netloc ("user:pass@host:5432"), path, query, fragment
    if parts.password is None:  # No password inside the URL: nothing to hide
        return url
    host = parts.hostname or ""  # The host name without credentials
    if parts.port:  # Keep the port if one was given
        host = f"{host}:{parts.port}"
    netloc = f"{parts.username}:****@{host}"  # Rebuild "user:****@host:port"
    return urlunsplit(parts._replace(netloc=netloc))  # Join the URL back together


def settings_summary(settings: Settings) -> dict[str, str]:
    """Turn settings into display strings, masking anything sensitive."""
    summary: dict[str, str] = {}  # field name -> safe display value
    for name in type(settings).model_fields:  # Iterate over the declared fields, in order
        value = getattr(settings, name)  # Read the field's current value
        if isinstance(value, SecretStr) or name.endswith("_api_key"):  # Any API key field
            summary[name] = mask_secret(value)
        elif name == "database_url":  # URLs can carry passwords too
            summary[name] = redact_url(value)
        else:  # Ordinary, non-secret values
            summary[name] = "(not set)" if value is None else str(value)
    return summary


def cmd_hello(args: argparse.Namespace, settings: Settings) -> int:
    """`brightdesk hello`: prove that the package is installed and runnable."""
    print("Hello from Brightdesk! Your workbench is ready.")  # Printing is fine in a CLI
    print(f"Hello, {args.name}! Your Brightdesk workbench is ready.")
    return 0  # Exit code 0 means success


def cmd_info(args: argparse.Namespace, settings: Settings) -> int:
    """`brightdesk info`: show the active configuration with secrets masked."""
    summary = settings_summary(settings)
    if args.json:
        payload = {"version": __version__, "python": platform.python_version(), "settings": summary}
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Brightdesk {__version__} (Python {platform.python_version()})")  # Header line
    for name, value in summary.items():  # One line per setting
        print(f"  {name:<18} {value}")  # :<18 left-aligns the name in an 18-char column
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Describe the command line: program name, global options and subcommands."""
    parser = argparse.ArgumentParser(
        prog="brightdesk",  # Name shown in --help and error messages
        description="Command-line tools for the Brightdesk Support Copilot.",
    )
    parser.add_argument(  # A global flag that prints the version and exits
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    # Subcommands work like `git commit` / `git push`: one program, several actions.
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    hello = commands.add_parser("hello", help="Print a greeting to check the install.")
    hello.add_argument("--name", default="there", help="who to greet (default: %(default)s).")
    hello.set_defaults(handler=cmd_hello)  # Remember which function handles this subcommand

    info = commands.add_parser("info", help="Show the configuration with secrets masked.")
    info.add_argument("--json", action="store_true", help="print info in json format")
    info.set_defaults(handler=cmd_info)

    return parser


def main(argv: Sequence[str] | None = None, *, settings: Settings | None = None) -> int:
    """Entry point. ``argv=None`` means "read sys.argv"; tests pass a list instead."""
    args = build_parser().parse_args(argv)  # Exits with code 2 and a usage message if invalid
    try:
        settings = settings or get_settings()  # Load .env + environment variables (once)
    except ValidationError as error:  # e.g. LLM_PROVIDER=gemini is not an allowed value
        print(f"Configuration error:\n{error}", file=sys.stderr)  # Errors go to stderr
        return 2  # Non-zero exit code tells the shell (and CI) that something failed
    handler: Handler = args.handler  # The function stored by set_defaults(...)
    return handler(args, settings)  # Run it and pass its exit code back


if __name__ == "__main__":  # Only true when run with `python -m ...`, not when imported
    raise SystemExit(main())  # Turn main()'s return value into the process exit code
