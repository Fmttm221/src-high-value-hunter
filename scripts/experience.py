import argparse
import datetime
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EXPERIENCE_DIR = BASE / "experience"
INDEX = EXPERIENCE_DIR / "INDEX.md"


def read_index() -> str:
    return INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""


def search(keyword: str) -> None:
    text = read_index()
    hits = []
    for line in text.splitlines():
        if keyword.lower() in line.lower():
            hits.append(line)
    if not hits:
        print("no experience matched")
        return
    for line in hits:
        print(line)
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2:
            filename = parts[1]
            path = EXPERIENCE_DIR / filename
            if path.exists():
                print("-" * 40)
                print(path.read_text(encoding="utf-8"))
                print("-" * 40)


def add(keyword: str) -> None:
    safe = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]+", "-", keyword).strip("-") or "experience"
    path = EXPERIENCE_DIR / f"{safe}.md"
    if path.exists():
        print(f"file exists: {path}")
        return
    today = datetime.date.today().isoformat()
    path.write_text(
        "# 现象\n\n# 原因\n\n# 解法\n\n# 验证\n\n"
        f"confidence: low\nlast_verified: {today}\n",
        encoding="utf-8",
    )
    with INDEX.open("a", encoding="utf-8") as fh:
        fh.write(f"| {keyword} | {path.name} | TODO |\n")
    print(f"created: {path}")


def list_index() -> None:
    print(read_index())


def main() -> None:
    parser = argparse.ArgumentParser(description="Experience library helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("keyword")

    p_add = sub.add_parser("add")
    p_add.add_argument("keyword")

    sub.add_parser("list")

    args = parser.parse_args()
    if args.command == "search":
        search(args.keyword)
    elif args.command == "add":
        add(args.keyword)
    elif args.command == "list":
        list_index()


if __name__ == "__main__":
    main()