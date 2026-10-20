"""Working Context aus Blöcken, Token-Schätzung je Block."""
import json

MEM_HEAD = ("Frühere Beobachtungen aus dem Episoden-Memory. "
            "Sie können veraltet oder falsch sein. Prüfe jede "
            "Angabe mit search oder read_lines, bevor du sie "
            "als Beleg verwendest.")


def est(text: str) -> int:
    """Faustregel: ein Token je vier Zeichen (Englisch)."""
    return (len(text) + 3) // 4


def msg_text(m: dict) -> str:
    """Inhalt einer Nachricht samt Tool Calls als Text."""
    text = str(m.get("content") or "")
    if m.get("tool_calls"):
        text += json.dumps(m["tool_calls"])
    return text


def memory_block(episodes: list[dict]) -> str:
    rows = [MEM_HEAD]
    for e in episodes:
        status = "verifiziert" if e["verified"] else "ungeprüft"
        rows.append(f"- [E{e['id']}, {e['created']}, {status}, "
                    f"Quelle: {e['source']}] {e['lesson']}")
    return "\n".join(rows)


def build(system: str, agents_md: str, episodes: list[dict],
          task: str, budget: int = 6000) -> list[dict]:
    """System, Projektwissen, Erinnerungen, Auftrag."""
    head = system
    if agents_md:
        head += "\n\nProjektwissen (AGENTS.md):\n" + agents_md
    keep = list(episodes)       # nach Relevanz sortiert
    while keep and (est(head) + est(task)
                    + est(memory_block(keep)) > budget):
        keep.pop()              # schwächste Erinnerung zuerst
    if est(head) + est(task) > budget:
        raise ValueError("Auftrag passt nicht ins Budget")
    msgs = [{"role": "system", "content": head}]
    if keep:
        msgs.append({"role": "system",
                     "content": memory_block(keep)})
    msgs.append({"role": "user", "content": task})
    return msgs


def inventory(messages: list[dict],
              tools: list[dict] = ()) -> dict:
    """Geschätzte Token je Herkunft, für einen Request."""
    inv = {"system": 0, "memory": 0, "auftrag": 0,
           "modell": 0, "observations": 0, "harness": 0,
           "tool_schemas": est(json.dumps(list(tools),
                                          ensure_ascii=False))}
    first_user = True
    for m in messages:
        text = msg_text(m)
        if m["role"] == "system":
            key = ("memory" if text.startswith(MEM_HEAD)
                   else "system")
        elif m["role"] == "user":
            key = "auftrag" if first_user else "harness"
            first_user = False
        else:
            key = {"assistant": "modell",
                   "tool": "observations"}[m["role"]]
        inv[key] += est(text)
    return inv
