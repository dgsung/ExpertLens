"""CLI entry point for ExpertLens."""

import argparse
import sys

from . import __version__
from .orchestrator import Orchestrator


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for ExpertLens CLI."""
    parser = argparse.ArgumentParser(
        prog="expertlens",
        description="ExpertLens - Search-grounded Expert Discovery System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m expertlens search "배터리 전문가" --lang ko
  python -m expertlens search "battery expert" --lang en
  python -m expertlens list
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search command
    search_parser = subparsers.add_parser(
        "search",
        help="Start a new expert search session",
    )
    search_parser.add_argument(
        "query",
        type=str,
        help="Search query (e.g., '배터리 전문가')",
    )
    search_parser.add_argument(
        "--lang",
        type=str,
        default="ko",
        choices=["ko", "en"],
        help="Session language (default: ko)",
    )

    # list command
    subparsers.add_parser(
        "list",
        help="List existing sessions",
    )

    return parser


def cmd_search(args: argparse.Namespace) -> int:
    """Handle the search command."""
    orchestrator = Orchestrator()
    result = orchestrator.run_search(query=args.query, language=args.lang)

    print(f"Session created: {result['session_id']}")
    print(f"Session file: {result['session_path']}")
    print(f"Report file: {result['report_path']}")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Handle the list command."""
    from pathlib import Path

    out_dir = Path("out")
    if not out_dir.exists():
        print("No sessions found (out/ directory does not exist)")
        return 0

    sessions = list(out_dir.glob("session-*.json"))
    if not sessions:
        print("No sessions found")
        return 0

    print(f"Found {len(sessions)} session(s):")
    for session_file in sorted(sessions):
        print(f"  - {session_file.name}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "search":
        return cmd_search(args)
    elif args.command == "list":
        return cmd_list(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
