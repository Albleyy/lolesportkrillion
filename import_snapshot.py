"""Build an interim quiz from GPTilt's Leaguepedia game snapshot.
Source: https://huggingface.co/datasets/gptilt/lol-esports-matches
Upstream: Leaguepedia contributors, CC BY-SA 3.0.
Does not infer player identities from team picks.
"""
import collections
import json
import math
from pathlib import Path

from datasets import load_dataset

def build(rows):
    groups = collections.defaultdict(dict)
    seen = set()
    def add(category, question, answer, event):
        if not isinstance(answer, str) or not answer.strip():
            return
        answer = answer.strip()
        group = groups[(category, question)]
        count, first = group.get(answer, (0, event))
        group[answer] = (count + 1, first)
    for row in rows:
        game = row.get("game_id")
        event = row.get("tournament")
        if not game or game in seen or not event:
            continue
        seen.add(game)
        for side in ("blue", "red"):
            team = row.get("team_" + side)
            if not team:
                continue
            add("Tournois", f"Cite une équipe ayant joué au tournoi {event}.", team, event)
            picks = {c for c in (row.get("picks_" + side) or []) if isinstance(c, str) and c.strip()}
            for champ in picks:
                add("Champions", f"Cite une équipe ayant joué {champ} en compétition.", team, event)
                add("Équipes", f"Cite un champion joué en compétition par {team}.", champ, event)
                add("Tournois", f"Cite un champion joué au tournoi {event}.", champ, event)
    bank = []
    for (category, question), answers in sorted(groups.items()):
        if len(answers) < 10:
            continue
        peak = max(n for n, _ in answers.values())
        entries = []
        for name, (count, event) in sorted(answers.items()):
            points = round(100 - 80 * math.log(count) / max(1, math.log(peak)))
            entries.append(dict(names=[name], p=points, source=event, games=count))
        bank.append([category, question, entries])
    if len(bank) < 7 or len(seen) < 1000:
        raise RuntimeError("Snapshot incomplete; refusing to replace bank")
    return bank, len(seen)

def main():
    rows = load_dataset("gptilt/lol-esports-matches", name="games", split="train")
    bank, games = build(rows)
    Path("bank.json").write_text(json.dumps(bank, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    meta = dict(mode="team_champion_snapshot", games=games, questions=len(bank),
                source="https://huggingface.co/datasets/gptilt/lol-esports-matches",
                upstream="https://lol.fandom.com/wiki/Leaguepedia",
                license="CC BY-SA 3.0", limitation="No individual player picks; coverage varies by competition.")
    Path("bank.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{games} games; {len(bank)} questions", flush=True)

if __name__ == "__main__":
    main()
