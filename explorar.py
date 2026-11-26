import ijson

with open("match_v5.json", "rb") as f:
    partida = next(ijson.items(f, "item"))

print("versão:", partida["info"]["gameVersion"])
print("duração (s):", partida["info"]["gameDuration"])
for p in partida["info"]["participants"]:
    if p["teamPosition"] == "TOP":
        print(p["championName"], "venceu" if p["win"] else "perdeu")
        print("campos do jogador:", sorted(p.keys()))
        print("runas:", p["perks"]["styles"][0]["selections"][0])
        print("feitiços:", p["summoner1Id"], p["summoner2Id"])
        print("challenges de lane:", {k: v for k, v in p["challenges"].items() if "aning" in k or "10Minutes" in k})
