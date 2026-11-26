"""Pós-rodada, reel: o previsto × real contado em cenas, para quem ainda não segue o perfil.

Gancho com a projeção e o real escondido (também é a capa, para não repetir a do carrossel
na grade), revelação do placar, titulares um a um no gráfico de halteres, destaques e
chamada para o site. Os números são os mesmos do carrossel.
Sai às 19:00 do dia do previsto-real; com --quando, 2 min depois do horário dado.
Renderizado com margem direita para a coluna de botões do Reels (config.FAIXA_DIREITA_REEL).
"""
from datetime import timedelta

from .. import config
from ..formato import num, sinal
from .comum import ctx, legenda, proximo
from .previsto_real import dados

PASSO = 0.4  # segundos por titular revelado


def montar(t, n, opcoes):
    v = dados(t, n, opcoes)
    d = v["d"]
    capa = ctx(d, real=v["real"], projecao=v["proj"], saldo=v["saldo"], comparacoes=v["comp"][:2])
    graf = ctx(d, chapeu="Jogador a jogador", titulo="Onde o modelo acertou e errou", itens=v["itens"], x=v["x"],
               nota_legenda="sem o 1,5× do capitão", rodape_texto=None)
    total = len(v["itens"])
    gancho = {**capa, "ocultar_real": True,
              "gancho": {"chapeu": f"O modelo projetou {num(v['proj'])}", "titulo": "Quanto o time", "marca": "fez?"}}

    cenas = [
        ("capa_resultado.html", gancho, 2.5, False),
        ("capa_resultado.html", capa, 3.5, True),
        ("halteres.html", {**graf, "revelados": 0}, 1.5, True),
        *[("halteres.html", {**graf, "revelados": i}, 3.5 if i == total else PASSO, False) for i in range(1, total + 1)],
        ("cartoes.html", ctx(d, chapeu="Quem decidiu", titulo="Destaques da rodada", cartoes=v["cartoes"]), 4.0, True),
        ("cta.html", ctx(d, chapeu="Toda rodada", titulo="Acerte ou erre, a gente mostra",
                         texto="Previsto × real de todas as rodadas no site.", itens=[]), 3.0, True),
    ]
    cap, melhor, pior = v["cap"], v["melhor"], v["pior"]
    texto = legenda(
        f"Rodada {n}: o modelo projetou {num(v['proj'])} pontos e o time fez {num(v['real'])} ({sinal(v['saldo'])}).",
        f"Melhor: {melhor['apelido']} ({num(melhor['pontos'], 1)}). Pior: {pior['apelido']} ({num(pior['pontos'], 1)}). "
        f"Capitão {cap['apelido']}: {num(cap['pontos'], 1)} pontos, "
        f"{num(cap['pontos'] * 1.5, 1) if cap['pontos'] is not None else '–'} com o 1,5×.",
        "Toda rodada o time é escalado antes do fechamento do mercado e publicado depois. O resultado sai depois do jogo, acerte ou erre. "
        "Times de especialistas entram só agregados, sem nome.",
        f"Todas as rodadas em {config.DOMINIO} (link na bio).",
        f"Quanto seu time fez? {config.HASHTAGS}",
    )
    return {
        "pauta": "reel-previsto-real", "formato": "reel", "cenas": cenas, "capa": ("capa_resultado.html", gancho),
        "legenda": texto,
        "agendado_para": (opcoes["quando"] + timedelta(minutes=2)) if opcoes.get("quando") else proximo(12).replace(hour=19),
        "expira_em": None,
        "origem": {"estado": d["estado"], "pontuado_em_utc": d["pontuado_em_utc"], "commit_modelo": d["modelo"]["commit"]},
    }
