"""Pós-rodada, story: previsto × real do time do modelo. Aponta para o carrossel do previsto-real.

Sai um minuto depois do previsto-real e só depois que ele estiver publicado: a chamada aponta para ele.
"""
from datetime import timedelta

from ..formato import num, sinal
from .comum import ctx, proximo
from .previsto_real import dados


def montar(t, n, opcoes):
    v = dados(t, n, opcoes)
    d = v["d"]
    return {
        "pauta": "story-resultado", "formato": "story", "legenda": "", "depende_de": "previsto-real",
        "slides": [("capa_resultado.html", ctx(d, real=v["real"], projecao=v["proj"], saldo=v["saldo"], comparacoes=v["comp"][:2],
                                               chamada="Jogador a jogador no post de hoje"),
                    f"Rodada {n}: o time do modelo fez {num(v['real'])} pontos contra {num(v['proj'])} projetados ({sinal(v['saldo'])}).")],
        "agendado_para": (opcoes.get("quando") or proximo(12)) + timedelta(minutes=1),
        "expira_em": None,
        "origem": {"estado": d["estado"], "pontuado_em_utc": d["pontuado_em_utc"], "commit_modelo": d["modelo"]["commit"]},
    }
