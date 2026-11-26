import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

d = pd.read_csv("confrontos_topo.csv")
X = d[["campeao", "inimigo"]]
y = d["venceu"]

# separa por partida: as duas linhas de um mesmo confronto ficam juntas
divisor = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
treino, teste = next(divisor.split(X, y, groups=d["matchId"]))


def novo_modelo():
    return Pipeline([
        ("codificar", ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["campeao", "inimigo"]),
        ])),
        ("regressao", LogisticRegression(C=0.5, max_iter=1000)),
    ])


modelo = novo_modelo()
modelo.fit(X.iloc[treino], y.iloc[treino])

prob = modelo.predict_proba(X.iloc[teste])[:, 1]
print("partidas de treino:", d.iloc[treino]["matchId"].nunique())
print("partidas de teste:", d.iloc[teste]["matchId"].nunique())
print("acurácia no teste:", round(accuracy_score(y.iloc[teste], prob > 0.5), 3), "(chute = 0.5)")
print("log loss no teste:", round(log_loss(y.iloc[teste], prob), 3), "(chute = 0.693)")

# modelo final: treina com todos os dados e salva
modelo = novo_modelo()
modelo.fit(X, y)
joblib.dump(modelo, "modelo_vitoria.joblib")
print("modelo salvo em modelo_vitoria.joblib")


def prever(campeao, inimigo):
    entrada = pd.DataFrame({"campeao": [campeao], "inimigo": [inimigo]})
    p = modelo.predict_proba(entrada)[0, 1]
    n = len(d[(d["campeao"] == campeao) & (d["inimigo"] == inimigo)])
    return p, n


print()
for a, b in [("Garen", "Jax"), ("Darius", "Garen"), ("Aatrox", "Sett")]:
    p, n = prever(a, b)
    print(f"{a} x {b}: {p:.1%} de vitória para {a} (base: {n} partidas)")