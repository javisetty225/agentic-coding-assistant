"""
Agentic Coding Assistant — CLI Entry Point
Usage:
    python src/main.py --interactive
    python src/main.py "Build a movie recommendation flow"
"""


import argparse
import os
import sys
from pathlib import Path

from agent.orchestrator import LangflowAgent

BANNER = """
╔══════════════════════════════════════════════════════════╗
║        AGENTIC CODING ASSISTANT  •  Pi-style harness     ║
╚══════════════════════════════════════════════════════════╝
"""

EXAMPLE_PROMPTS = [
    "Build a text summarization chatbot flow with an OpenAI model",
    "Create a RAG (Retrieval Augmented Generation) flow with a vector store",
    "Build a sentiment analysis flow with a custom Python component",
    "Create a vision flow that accepts image uploads and describes them using Claude",
    "Build a movie recommendation flow with MovieFilterComponent for genre and mood filtering",
]


def save_artifacts(artifacts: dict, output_dir: str = "generated") -> list[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    for fname, content in artifacts.items():
        dest = out / fname
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        saved.append(str(dest))
    return saved


def print_summary(artifacts: dict, tool_log: list) -> None:
    print("\n" + "─" * 60)
    print("✓  Generation complete")
    print("─" * 60)
    print(f"   Files generated : {len(artifacts)}")
    print(f"   Tool calls made : {len(tool_log)}")
    print("\n   Artifacts:")
    for fname, content in artifacts.items():
        print(f"     • {fname:40s}  ({len(content):,} chars)")
    print()


def run_agent(
    description: str,
    output_dir: str = "generated",
    api_key: str | None = None,
) -> dict:
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: set ANTHROPIC_API_KEY environment variable or pass --api-key")
        sys.exit(1)

    print(BANNER)
    print(f"Task: {description}\n")
    print("Running agent loop…\n")

    agent = LangflowAgent(api_key=api_key)
    artifacts = agent.run(description)

    print_summary(artifacts, agent.tool_calls_log)

    if artifacts:
        saved = save_artifacts(artifacts, output_dir)
        print(f"   Saved to: ./{output_dir}/")
        for f in saved:
            print(f"     {f}")
    else:
        print("WARNING: agent produced no artifacts. Check API key and model access.")

    return artifacts


def interactive_mode(api_key: str | None = None) -> None:
    print(BANNER)
    print("Interactive mode. Type 'quit' to exit.\n")
    print("Example prompts:")
    for i, p in enumerate(EXAMPLE_PROMPTS, 1):
        print(f"  {i}. {p}")
    print()

    while True:
        try:
            description = input("Describe your Langflow flow: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if description.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        if not description:
            continue

        if description.isdigit():
            idx = int(description) - 1
            if 0 <= idx < len(EXAMPLE_PROMPTS):
                description = EXAMPLE_PROMPTS[idx]
                print(f"→ {description}\n")

        run_agent(description, api_key=api_key)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agentic Coding Assistant — generate Langflow flows from natural language"
    )
    parser.add_argument(
        "description", nargs="?",
        help="Natural language description of the flow to build",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--output-dir", "-o", default="generated",
        help="Output directory for artifacts",
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    args = parser.parse_args()

    if args.interactive:
        interactive_mode(api_key=args.api_key)
    elif args.description:
        run_agent(args.description, output_dir=args.output_dir, api_key=args.api_key)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()