import ijson
from collections import Counter

CAMPEOES = {"Darius", "Malphite", "Yone", "Aatrox", "Jax",
            "Renekton", "Garen", "Mordekaiser", "Jayce", "Sett"}

total = 0
com_dois_topos = 0
entre_os_10 = 0
pares = Counter()
patches = Counter()

with open("match_v5.json", "rb") as f:
    for partida in ijson.items(f, "item"):
        total += 1
        info = partida["info"]
        patches[".".join(info["gameVersion"].split(".")[:2])] += 1
        topo = [p for p in info["participants"] if p.get("teamPosition") == "TOP"]
        if len(topo) == 2 and topo[0]["teamId"] != topo[1]["teamId"]:
            com_dois_topos += 1
            a, b = topo[0]["championName"], topo[1]["championName"]
            if a in CAMPEOES and b in CAMPEOES:
                entre_os_10 += 1
                pares[tuple(sorted((a, b)))] += 1
        if total % 1000 == 0:
            print("lidas:", total, flush=True)

print()
print("partidas lidas:", total)
print("com um topo de cada time:", com_dois_topos)
print("entre os 10 campeões:", entre_os_10)
print("patches:", patches.most_common(5))
print("pares com 30+ partidas:", sum(1 for n in pares.values() if n >= 30), "de", len(pares), "pares vistos")
print("5 pares com mais partidas:")
for par, n in pares.most_common(5):
    print(" ", par, n)
print("5 pares com menos partidas:")
for par, n in pares.most_common()[-5:]:
    print(" ", par, n)
