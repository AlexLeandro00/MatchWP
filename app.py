import json
import math
from collections import Counter
from pathlib import Path

import joblib
import pandas as pd
import requests
import streamlit as st

PASTA = Path(__file__).parent
VERSAO = "14.24.1"  # versão do Data Dragon, da mesma época das partidas da base
DDRAGON = f"https://ddragon.leagueoflegends.com/cdn/{VERSAO}"

TOP10 = ["Darius", "Malphite", "Yone", "Aatrox", "Jax",
         "Renekton", "Garen", "Mordekaiser", "Jayce", "Sett"]
ITENS = [f"item{i}" for i in range(6)]
MIN_PARTIDAS = 30
ACURACIA_VITORIA = "50,8%"  # resultado do treinar.py no teste
ACURACIA_LANE = "57,1%"  # resultado do treinar_lane.py no teste

st.set_page_config(page_title="MatCh.wp", page_icon="⚔️", layout="wide")


# ---------- carregamento ----------

@st.cache_data
def carregar_dados():
    return pd.read_csv(PASTA / "confrontos_topo.csv", dtype={"patch": str})


@st.cache_resource
def carregar_modelos():
    return (joblib.load(PASTA / "modelo_vitoria.joblib"),
            joblib.load(PASTA / "modelo_lane.joblib"))


@st.cache_data
def carregar_dicas():
    with open(PASTA / "dicas_matchup.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600)
def carregar_nomes():
    """Traduz IDs de itens, runas e feitiços usando o Data Dragon (Riot)."""
    nomes = {"itens": {}, "itens_ouro": {}, "runas": {}, "feiticos": {}}
    try:
        itens = requests.get(f"{DDRAGON}/data/pt_BR/item.json", timeout=10).json()["data"]
        for id_, item in itens.items():
            nomes["itens"][int(id_)] = item["name"]
            nomes["itens_ouro"][int(id_)] = item["gold"]["total"]
        arvores = requests.get(f"{DDRAGON}/data/pt_BR/runesReforged.json", timeout=10).json()
        for arvore in arvores:
            nomes["runas"][arvore["id"]] = arvore["name"]
            for faixa in arvore["slots"]:
                for runa in faixa["runes"]:
                    nomes["runas"][runa["id"]] = runa["name"]
        feiticos = requests.get(f"{DDRAGON}/data/pt_BR/summoner.json", timeout=10).json()["data"]
        for feitico in feiticos.values():
            nomes["feiticos"][int(feitico["key"])] = feitico["name"]
    except Exception:
        pass  # sem internet, a página mostra os números (IDs) no lugar dos nomes
    return nomes


# ---------- funções de apoio ----------

def pct(x):
    return f"{x * 100:.1f}%".replace(".", ",")


def intervalo_wilson(k, n, z=1.96):
    """Intervalo de confiança de 95% para uma taxa de vitória."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    centro = p + z * z / (2 * n)
    margem = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    base = 1 + z * z / n
    return (centro - margem) / base, (centro + margem) / base


def tabela_percentual(contagem, total, nomear):
    return pd.DataFrame(
        {"% dos vencedores": [pct(v / total) for v in contagem.values()]},
        index=[nomear(i) for i in contagem.keys()],
    )


dados = carregar_dados()
modelo_vitoria, modelo_lane = carregar_modelos()
dicas = carregar_dicas()
nomes = carregar_nomes()


def nome_item(i):
    return nomes["itens"].get(int(i), f"Item {int(i)}")


def nome_runa(i):
    return nomes["runas"].get(int(i), f"Runa {int(i)}")


def nome_feitico(i):
    return nomes["feiticos"].get(int(i), f"Feitiço {int(i)}")


# ---------- cabeçalho e escolha do confronto ----------

st.title("⚔️ MatCh.wp")
st.caption("Estratégia para a rota de topo de League of Legends, "
           "a partir de partidas reais da API da Riot.")

c1, c2, c3 = st.columns([5, 1, 5])
with c1:
    meu = st.selectbox("Seu campeão", TOP10, index=TOP10.index("Garen"))
    st.image(f"{DDRAGON}/img/champion/{meu}.png", width=88)
with c2:
    st.markdown("<h2 style='text-align:center; margin-top:2.2rem'>vs</h2>",
                unsafe_allow_html=True)
with c3:
    outros = [c for c in TOP10 if c != meu]
    inimigo = st.selectbox("Campeão inimigo", outros,
                           index=outros.index("Jax") if "Jax" in outros else 0)
    st.image(f"{DDRAGON}/img/champion/{inimigo}.png", width=88)

confronto = dados[(dados["campeao"] == meu) & (dados["inimigo"] == inimigo)]
n = len(confronto)
k = int(confronto["venceu"].sum())
entrada = pd.DataFrame({"campeao": [meu], "inimigo": [inimigo]})
p_modelo = float(modelo_vitoria.predict_proba(entrada)[0, 1])

m1, m2, m3 = st.columns(3)
m1.metric("Chance de vitória (modelo)", pct(p_modelo))
if n:
    inf, sup = intervalo_wilson(k, n)
    m2.metric("Nas partidas da base", pct(k / n))
    m2.caption(f"{k} vitórias em {n} partidas")
    m3.metric("Margem de erro (95%)", f"{pct(inf)} a {pct(sup)}")
else:
    m2.metric("Nas partidas da base", "sem partidas")

if n < MIN_PARTIDAS:
    st.warning(f"Só {n} partidas de {meu} contra {inimigo} na base. "
               "Com tão poucas, o percentual muda muito de uma amostra para outra.")
st.caption(f"O modelo acertou {ACURACIA_VITORIA} dos resultados no teste (chutar dá 50%): "
           "saber só os dois campeões ajuda pouco a prever o vencedor.")

aba_dicas, aba_build, aba_lane, aba_dados = st.tabs(
    ["Como jogar contra", "Runas, feitiços e itens", "Começo de jogo", "Sobre os dados"])

# ---------- aba 1: dicas escritas ----------

with aba_dicas:
    info = dicas["campeoes"].get(inimigo, {})
    lista = list(info.get("dicas", []))
    st.subheader(f"Como jogar contra {inimigo}")
    if inimigo == "Jax":
        if meu == "Garen":
            st.caption("Dicas escritas pelo Alex, jogando de Garen contra Jax.")
        else:
            lista = lista[3:]  # as 3 primeiras são específicas do Garen
    elif info.get("resumo"):
        st.write(info["resumo"])
    for dica in lista:
        st.markdown(f"- {dica}")
    if meu == "Jax" and inimigo == "Garen":
        st.markdown("**Dicas do Alex, jogando de Jax contra Garen**")
        for dica in info.get("dicas_do_alex", []):
            st.markdown(f"- {dica}")
    fontes = info.get("fontes", [])
    if fontes:
        with st.expander("Fontes das dicas"):
            for fonte in fontes:
                st.markdown(f"- {fonte}")

# ---------- aba 2: runas, feitiços e itens dos vencedores ----------

with aba_build:
    vencedores = confronto[confronto["venceu"] == 1]
    if len(vencedores) >= 10:
        amostra = vencedores
        origem = f"{len(amostra)} vitórias de {meu} contra {inimigo}"
    else:
        amostra = dados[(dados["campeao"] == meu) & (dados["venceu"] == 1)]
        origem = (f"{len(amostra)} vitórias de {meu} contra qualquer inimigo "
                  f"(há poucas contra {inimigo})")
    st.caption(f"Baseado em {origem}.")
    total = len(amostra)
    if total == 0:
        st.info("Sem partidas para mostrar.")
    else:
        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown("**Runa principal**")
            runas = amostra["runa_principal"].value_counts().head(3)
            st.table(tabela_percentual(runas.to_dict(), total, nome_runa))
        with b2:
            st.markdown("**Feitiços**")
            pares = Counter(zip(amostra["feitico1"], amostra["feitico2"])).most_common(3)
            st.table(tabela_percentual(
                {par: v for par, v in pares}, total,
                lambda par: " + ".join(nome_feitico(x) for x in par)))
        with b3:
            st.markdown("**Itens finais**")
            itens = pd.Series(amostra[ITENS].values.ravel()).dropna().astype(int)
            itens = itens[itens > 0]
            if nomes["itens_ouro"]:  # só itens completos, sem componentes
                itens = itens[itens.map(lambda i: nomes["itens_ouro"].get(i, 0) >= 900)]
            st.table(tabela_percentual(itens.value_counts().head(6).to_dict(), total, nome_item))

# ---------- aba 3: começo de jogo (modelo 2) ----------

with aba_lane:
    st.subheader("Começo de jogo (até os 10 minutos)")
    lane = dados.dropna(subset=["cs10", "cs10_inimigo", "vantagem_early", "vantagem_lane"]).copy()
    lane["dif_cs10"] = lane["cs10"] - lane["cs10_inimigo"]
    meus = lane[lane["campeao"] == meu]

    if len(meus) >= MIN_PARTIDAS:
        mediana_v = meus[meus["venceu"] == 1]["cs10"].median()
        mediana_d = meus[meus["venceu"] == 0]["cs10"].median()
        if mediana_v - mediana_d >= 3:
            st.write(f"Quem vence com {meu} costuma ter cerca de {mediana_v:.0f} CS aos 10 minutos, "
                     f"contra {mediana_d:.0f} de quem perde. Vale priorizar o farm.")
        else:
            st.write(f"Com {meu}, o CS aos 10 minutos quase não separa vitória de derrota "
                     f"nesta base ({mediana_v:.0f} x {mediana_d:.0f}). Outros fatores pesam mais.")

        rotulos = ["1 · 11+ atrás", "2 · 6 a 10 atrás", "3 · equilibrado (±5)",
                   "4 · 6 a 10 à frente", "5 · 11+ à frente"]
        faixas = pd.cut(meus["dif_cs10"], bins=[-1000, -11, -6, 5, 10, 1000], labels=rotulos)
        resumo = meus.groupby(faixas, observed=True)["venceu"].agg(["mean", "count"])
        resumo.columns = ["Vitórias (%)", "Jogadores"]
        resumo["Vitórias (%)"] = (resumo["Vitórias (%)"] * 100).round(1)
        st.markdown(f"**Taxa de vitória de {meu} pela diferença de CS aos 10 minutos**")
        st.bar_chart(resumo["Vitórias (%)"])
        st.table(resumo)

    st.markdown("**Simule a sua lane**")
    dif = st.slider("Diferença de CS para o inimigo aos 10 minutos", -30, 30, 0)
    vantagem = st.checkbox("Estou com vantagem de ouro e XP na lane")
    simulacao = pd.DataFrame({"dif_cs10": [dif],
                              "vantagem_early": [int(vantagem)],
                              "vantagem_lane": [int(vantagem)]})
    p_lane = float(modelo_lane.predict_proba(simulacao)[0, 1])
    st.metric("Chance de vitória (modelo da lane)", pct(p_lane))
    st.caption(f"O modelo da lane acertou {ACURACIA_LANE} no teste. Ele usa informação de dentro "
               "da partida, então serve para orientar o jogo e não para prever antes dele. "
               "Meio e fim de jogo precisariam da timeline da Riot, que ficou fora desta versão.")

# ---------- aba 4: sobre os dados ----------

with aba_dados:
    patches = sorted(dados["patch"].unique(), key=lambda s: tuple(int(x) for x in s.split(".")))
    st.markdown(f"""
- **Base:** partidas ranqueadas da API da Riot (região EUW), do patch {patches[0]} ao {patches[-1]},
  de um conjunto público do Hugging Face (AngryBacteria/league_of_legends).
- **Confrontos de topo usados:** {dados['matchId'].nunique()} partidas.
- **Modelo 1 (chance de vitória):** usa só os dois campeões. Acerto no teste: {ACURACIA_VITORIA}.
- **Modelo 2 (começo de jogo):** usa CS e vantagem na lane. Acerto no teste: {ACURACIA_LANE}.

**Limitações**
- Poucas partidas por confronto: por isso o site mostra a quantidade e a margem de erro.
- Os dados são de 2023 e 2024, e o jogo muda a cada patch.
- Correlação não é causa: quem está ganhando a lane naturalmente farma mais.
- Dicas de meio e fim de jogo ficaram de fora (exigem a timeline de 14,5 GB).
""")
    st.caption("Projeto acadêmico. MatCh.wp não é endossado pela Riot Games e não reflete as "
               "opiniões da Riot Games nem de quem trabalha com as propriedades da Riot Games. "
               "League of Legends e Riot Games são marcas registradas da Riot Games, Inc.")