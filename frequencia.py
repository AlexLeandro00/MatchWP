import ijson
from collections import Counter

freq = Counter()
confrontos = []

with open("match_v5.json", "rb") as f:
    for partida in ijson.items(f, "item"):
        topo = [p for p in partida["info"]["participants"] if p.get("teamPosition") == "TOP"]
        if len(topo) == 2 and topo[0]["teamId"] != topo[1]["teamId"]:
            a, b = topo[0]["championName"], topo[1]["championName"]
            freq[a] += 1
            freq[b] += 1
            confrontos.append((a, b))

print("Campeões mais jogados no topo nesta base:")
for nome, n in freq.most_common(20):
    print(f"  {nome}: {n} ({n / (2 * len(confrontos)) * 100:.1f}%)")

for tamanho in (10, 15, 20):
    grupo = {nome for nome, _ in freq.most_common(tamanho)}
    pares = Counter(tuple(sorted(c)) for c in confrontos if c[0] in grupo and c[1] in grupo and c[0] != c[1])
    print(f"\nTop {tamanho} da base: {sum(pares.values())} confrontos, {sum(1 for n in pares.values() if n >= 30)} pares com 30+ partidas, de {len(pares)} pares vistos")
