import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TOP10 = ["Darius", "Malphite", "Yone", "Aatrox", "Jax",
         "Renekton", "Garen", "Mordekaiser", "Jayce", "Sett"]

d = pd.read_csv("confrontos_topo.csv")
d = d.dropna(subset=["cs10", "cs10_inimigo", "vantagem_early", "vantagem_lane"])
d["dif_cs10"] = d["cs10"] - d["cs10_inimigo"]

COLUNAS = ["dif_cs10", "vantagem_early", "vantagem_lane"]
X = d[COLUNAS]
y = d["venceu"]

# separa por partida: as duas linhas de um mesmo confronto ficam juntas
divisor = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
treino, teste = next(divisor.split(X, y, groups=d["matchId"]))

modelo = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
modelo.fit(X.iloc[treino], y.iloc[treino])

prob = modelo.predict_proba(X.iloc[teste])[:, 1]
print("MODELO 2: quem vence a partir da fase de lane")
print("acurácia no teste:", round(accuracy_score(y.iloc[teste], prob > 0.5), 3), "(chute = 0.5)")
print("log loss no teste:", round(log_loss(y.iloc[teste], prob), 3), "(chute = 0.693)")

print("\nPeso de cada fator (quanto maior, mais ajuda a vencer):")
for nome, peso in zip(COLUNAS, modelo[-1].coef_[0]):
    print(f"  {nome}: {peso:+.2f}")

joblib.dump(modelo, "modelo_lane.joblib")
print("\nmodelo salvo em modelo_lane.joblib")

print("\nTaxa de vitória pela diferença de CS aos 10 minutos:")
faixas = [
    ("à frente (5 CS ou mais)", d["dif_cs10"] >= 5),
    ("equilibrado (-4 a +4)", d["dif_cs10"].between(-4, 4)),
    ("atrás (5 CS ou menos)", d["dif_cs10"] <= -5),
]
for rotulo, filtro in faixas:
    sub = d[filtro]
    print(f"  {rotulo}: {sub['venceu'].mean():.1%} de vitória ({len(sub)} jogadores)")

print("\nTaxa de vitória com o marcador de vantagem da Riot:")
for col in ["vantagem_early", "vantagem_lane"]:
    for valor in (1, 0):
        sub = d[d[col] == valor]
        print(f"  {col} = {valor}: {sub['venceu'].mean():.1%} de vitória ({len(sub)} jogadores)")

print("\nPor campeão (CS mediano aos 10 min de quem venceu x quem perdeu):")
for c in TOP10:
    sub = d[d["campeao"] == c]
    if len(sub) < 30:
        continue
    v = sub[sub["venceu"] == 1]
    p = sub[sub["venceu"] == 0]
    print(f"  {c}: {v['cs10'].median():.0f} (vitória) x {p['cs10'].median():.0f} (derrota), {len(sub)} partidas")