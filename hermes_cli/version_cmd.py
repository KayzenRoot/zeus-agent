"""`hermes --version` handler, kept out of the CLI facade."""


def cmd_version(args):
    """Show version (--version/-V flag)."""
    from hermes_cli.main import _print_version_info

    _print_version_info(check_updates=True)
