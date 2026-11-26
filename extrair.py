import csv
import ijson

CAMPOS = [
    "matchId", "patch", "duracao", "campeao", "inimigo", "venceu",
    "estilo_principal", "runa_principal", "estilo_secundario",
    "feitico1", "feitico2",
    "item0", "item1", "item2", "item3", "item4", "item5",
    "cs10", "cs10_inimigo", "vantagem_early", "vantagem_lane",
    "kills", "deaths", "assists", "ouro", "visao",
]


def linha(partida, eu, ele):
    info = partida["info"]
    est = eu["perks"]["styles"]
    ch, ch_ele = eu.get("challenges") or {}, ele.get("challenges") or {}
    feiticos = sorted((eu["summoner1Id"], eu["summoner2Id"]))
    return {
        "matchId": partida["metadata"]["matchId"],
        "patch": ".".join(info["gameVersion"].split(".")[:2]),
        "duracao": info["gameDuration"],
        "campeao": eu["championName"],
        "inimigo": ele["championName"],
        "venceu": int(eu["win"]),
        "estilo_principal": est[0]["style"],
        "runa_principal": est[0]["selections"][0]["perk"],
        "estilo_secundario": est[1]["style"],
        "feitico1": feiticos[0],
        "feitico2": feiticos[1],
        **{f"item{i}": eu[f"item{i}"] for i in range(6)},
        "cs10": ch.get("laneMinionsFirst10Minutes", ""),
        "cs10_inimigo": ch_ele.get("laneMinionsFirst10Minutes", ""),
        "vantagem_early": ch.get("earlyLaningPhaseGoldExpAdvantage", ""),
        "vantagem_lane": ch.get("laningPhaseGoldExpAdvantage", ""),
        "kills": eu["kills"],
        "deaths": eu["deaths"],
        "assists": eu["assists"],
        "ouro": eu["goldEarned"],
        "visao": eu["visionScore"],
    }


total = 0
confrontos = 0

with open("match_v5.json", "rb") as f, open("confrontos_topo.csv", "w", newline="", encoding="utf-8") as saida:
    escritor = csv.DictWriter(saida, fieldnames=CAMPOS)
    escritor.writeheader()
    for partida in ijson.items(f, "item"):
        total += 1
        topo = [p for p in partida["info"]["participants"] if p.get("teamPosition") == "TOP"]
        if len(topo) == 2 and topo[0]["teamId"] != topo[1]["teamId"]:
            a, b = topo
            if a["championName"] != b["championName"] and not a.get("gameEndedInEarlySurrender"):
                escritor.writerow(linha(partida, a, b))
                escritor.writerow(linha(partida, b, a))
                confrontos += 1
        if total % 2000 == 0:
            print("lidas:", total, flush=True)

print("partidas lidas:", total)
print("confrontos salvos:", confrontos, "(", confrontos * 2, "linhas )")