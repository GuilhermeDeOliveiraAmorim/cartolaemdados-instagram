"""Pré-rodada, story: o time do modelo saiu. Projeção, esquema e capitão, e aponta para o carrossel.

Sai um minuto depois do time-modelo, então nunca antes do fechamento do mercado, e só depois que
o time-modelo estiver publicado: a chamada aponta para ele.
"""
from datetime import timedelta

from .. import fonte
from ..formato import num
from .comum import apos_fechamento, ctx


def montar(t, n, opcoes):
    d = fonte.diario(t, n)
    if d["estado"] != "aberta" and not opcoes.get("forcar"):
        raise fonte.ErroFonte(f"rodada {n} já está fechada; o story do time sai entre o fechamento e o pós")
    tm = d["time"]
    cap = next(a for a in d["atletas"] if a["papel"] == "titular" and a["capitao"])
    return {
        "pauta": "story-time", "formato": "story", "legenda": "", "depende_de": "time-modelo",
        "slides": [("capa_time.html", ctx(d, time=tm, capitao=cap, chamada="Escalação completa no post de hoje"),
                    f"O time do modelo para a rodada {n}: {num(tm['projecao'])} pontos projetados, {tm['esquema']}, "
                    f"capitão {cap['apelido']}.")],
        "agendado_para": apos_fechamento(fonte.fechamento(t, n), opcoes) + timedelta(minutes=1),
        "expira_em": None,
        "origem": {"estado": d["estado"], "escalado_em_utc": d["escalado_em_utc"], "commit_modelo": d["modelo"]["commit"]},
    }
