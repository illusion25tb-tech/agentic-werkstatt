"""Zwei Kurzschreibweisen: := und match."""


def check_diff(diff: str) -> str | None:
    return "leerer Diff" if not diff.strip() else None


if reason := check_diff("   "):
    print("abgelehnt:", reason)


def react(effect: str) -> str:
    match effect:
        case "timeout":
            return "neu starten"
        case "budget" | "red":
            return "an Menschen übergeben"
        case _:
            return "protokollieren"


for effect in ["timeout", "red", "empty_diff"]:
    print(effect, "->", react(effect))
