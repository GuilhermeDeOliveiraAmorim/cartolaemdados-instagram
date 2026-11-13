"""Pré-rodada: o time escalado pelo modelo, banco, Luxo e o consenso que ficou de fora."""
from datetime import timedelta

from .. import config, fonte
from ..formato import num, cartoletas
from .comum import agora, ctx, legenda, numerar


def _linhas(titulares):
    por = {p: [a for a in titulares if a["posicao"] == p] for p in ("GOL", "LAT", "ZAG", "MEI", "ATA")}
    lat, zag = por["LAT"], por["ZAG"]
    defesa = ([lat[0]] + zag + [lat[1]]) if len(lat) == 2 else (lat + zag)
    return [l for l in (por["ATA"], por["MEI"], defesa, por["GOL"]) if l]


def montar(t, n, opcoes):
    d = fonte.diario(t, n)
    if d["estado"] != "aberta" and not opcoes.get("forcar"):
        raise fonte.ErroFonte(f"rodada {n} já está fechada; o time do modelo é post de antes do fechamento")
    tit = [a for a in d["atletas"] if a["papel"] == "titular"]
    banco = [a for a in d["atletas"] if a["papel"] != "titular"]
    tec = next((a for a in tit if a["posicao"] == "TEC"), None)
    cap = next(a for a in tit if a["capitao"])
    tm = d["time"]
    consenso = d.get("consenso") or []

    slides = numerar([
        ("capa_time.html", ctx(d, time=tm, capitao=cap),
         f"Capa: o time do modelo para a rodada {n}, {num(tm['projecao'])} pontos projetados, esquema {tm['esquema']}, capitão {cap['apelido']}."),
        ("campo.html", ctx(d, time=tm, linhas=_linhas([a for a in tit if a['posicao'] != 'TEC']), tecnico=tec),
         "Campo com os titulares: " + "; ".join(f"{a['posicao']} {a['apelido']} ({a['clube']}), projeção {num(a['proj'])}" for a in tit) + "."),
        ("banco.html", ctx(d, banco=banco, consenso=consenso[:4]),
         "Banco: " + "; ".join(f"{a['posicao']} {a['apelido']}" for a in banco) + ". "
         + ("Consenso fora do time: " + "; ".join(f"{c['apelido']} em {c['times']} times" for c in consenso[:4]) + "." if consenso else "")),
        ("cta.html", ctx(d, chapeu="Depois da rodada", titulo="Previsto × real",
                         texto="Depois do jogo a gente volta com o resultado: quanto o time fez contra o que o modelo projetou.",
                         itens=["Projeção é a pontuação média esperada, não garantia.",
                                "Azul é sempre o previsto pelo modelo.",
                                "Escalação, projeção e histórico de todas as rodadas no site."]),
         f"Chamada para o site {config.DOMINIO}."),
    ])

    destaques = sorted(tit, key=lambda a: -(a["proj"] or 0))[:3]
    texto = legenda(
        f"O time do modelo para a rodada {n} do Cartola: {num(tm['projecao'])} pontos projetados no {tm['esquema']}, "
        f"custando {cartoletas(tm['custo'])}.",
        f"Capitão: {cap['apelido']} ({cap['clube']} x {cap['adversario']}), projeção de {num(cap['proj'])}.\n"
        + "Maiores projeções: " + ", ".join(f"{a['apelido']} {num(a['proj'])}" for a in destaques) + ".",
        "A escalação sai de um modelo treinado com o histórico do Cartola desde 2021 e validado rodada a rodada. "
        "Depois da rodada a gente posta o previsto × real, acerte ou erre.",
        f"Diário completo em {config.DOMINIO} (link na bio).",
        f"Quem você colocaria de capitão? {config.HASHTAGS}",
    )
    fecha = fonte.fechamento(t, n)
    return {
        "pauta": "time-modelo", "slides": slides, "legenda": texto,
        "agendado_para": opcoes.get("quando") or agora(),
        "expira_em": fecha - timedelta(minutes=10) if fecha else None,
        "origem": {"estado": d["estado"], "escalado_em_utc": d["escalado_em_utc"], "commit_modelo": d["modelo"]["commit"]},
    }
