"""Pós-rodada: quanto o time do modelo fez contra o que projetou, jogador a jogador."""
import statistics

from .. import config, fonte
from ..formato import num, sinal
from .comum import ctx, legenda, numerar, proximo

ORDEM = {"GOL": 0, "LAT": 1, "ZAG": 2, "MEI": 3, "ATA": 4, "TEC": 5}


def escala(valores, folga=0.06):
    lo, hi = min(0, *valores), max(0, *valores)
    pad = (hi - lo) * folga
    lo, hi = lo - pad, hi + pad
    return lambda v: round((v - lo) / (hi - lo) * 100, 2)


def sugeridos_pontos(d):
    return [s["pontos"] for s in d.get("sugeridos") or [] if s["objetivo"] == "pontos" and s["pontos"] is not None]


def montar(t, n, opcoes):
    d = fonte.diario(t, n, opcoes.get("media_cartola"))
    if d["estado"] != "fechada":
        raise fonte.ErroFonte(f"rodada {n} ainda aberta; rode o /pos-rodada no cartola-dados antes")
    real, proj = d["resultado"]["pontos"], d["time"]["projecao"]
    tit = sorted([a for a in d["atletas"] if a["papel"] == "titular"], key=lambda a: ORDEM[a["posicao"]])
    jogaram = [a for a in tit if a["pontos"] is not None]
    cap = next(a for a in tit if a["capitao"])
    luxo = next((a for a in d["atletas"] if a["papel"] == "reserva_de_luxo"), None)

    comp = []
    if d["resultado"].get("media_cartola") is not None:
        comp.append({"texto": "Média dos times do Cartola", "valor": num(d["resultado"]["media_cartola"])})
    sp = sugeridos_pontos(d)
    if sp:
        comp.append({"texto": f"Mediana de {len(sp)} times de especialistas acompanhados", "valor": num(statistics.median(sp))})
        comp.append({"texto": "Times acompanhados que fizeram mais que o modelo", "valor": f"{sum(p > real for p in sp)} de {len(sp)}"})
    subs = d["resultado"].get("substituicoes")
    if subs is not None:
        comp.append({"texto": "Substituições automáticas do banco", "valor": str(subs)})

    itens = [{"rotulo": a["posicao"], "nome": a["apelido"], "capitao": a["capitao"], "prev": a["proj"], "real": a["pontos"]} for a in tit]
    x = escala([v for i in itens for v in (i["prev"], i["real"]) if v is not None])

    melhor = max(jogaram, key=lambda a: a["pontos"])
    pior = min(jogaram, key=lambda a: a["pontos"])
    cartoes = [
        {"etiqueta": "Melhor do time", "nome": melhor["apelido"], "linha": f"{melhor['posicao']} · {melhor['clube']} x {melhor['adversario']}",
         "valor": num(melhor["pontos"], 1), "sub": f"proj. {num(melhor['proj'], 1)}", "classe": "pos"},
        {"etiqueta": "Pior do time", "nome": pior["apelido"], "linha": f"{pior['posicao']} · {pior['clube']} x {pior['adversario']}",
         "valor": num(pior["pontos"], 1), "sub": f"proj. {num(pior['proj'], 1)}", "classe": "neg" if pior["pontos"] < 0 else ""},
        {"etiqueta": "Capitão (1,5×)", "nome": cap["apelido"], "linha": f"{cap['clube']} x {cap['adversario']} · fez {num(cap['pontos'], 1)}",
         "valor": num(cap["pontos"] * 1.5, 1) if cap["pontos"] is not None else "–", "sub": f"proj. {num(cap['proj'] * 1.5, 1)}",
         "classe": "neg" if (cap["pontos"] or 0) < 0 else ""},
    ]
    if luxo:
        cartoes.append({"etiqueta": "Reserva de Luxo", "nome": luxo["apelido"], "linha": f"{luxo['posicao']} · {luxo['clube']} x {luxo['adversario']}",
                        "valor": num(luxo["pontos"], 1), "sub": f"proj. {num(luxo['proj'], 1)}"})

    saldo = real - proj
    slides = numerar([
        ("capa_resultado.html", ctx(d, real=real, projecao=proj, saldo=saldo, comparacoes=comp),
         f"Rodada {n}: o time do modelo fez {num(real)} pontos contra {num(proj)} projetados ({sinal(saldo)})."),
        ("halteres.html", ctx(d, chapeu="Jogador a jogador", titulo="Onde o modelo acertou e errou", itens=itens, x=x,
                              nota_legenda="pontos sem o 1,5× do capitão", rodape_texto=None),
         "Gráfico de previsto contra real por titular: " + "; ".join(
             f"{i['nome']} previsto {num(i['prev'], 1)}, real {num(i['real'], 1) if i['real'] is not None else 'não jogou'}" for i in itens) + "."),
        ("cartoes.html", ctx(d, chapeu="Quem decidiu", titulo="Destaques da rodada", cartoes=cartoes),
         "Destaques: " + "; ".join(f"{c['etiqueta']} {c['nome']} {c['valor']}" for c in cartoes) + "."),
        ("cta.html", ctx(d, chapeu="Toda rodada", titulo="Acerte ou erre, a gente mostra",
                         texto="O modelo publica o time antes do fechamento e o resultado depois. Sem apagar rodada ruim.",
                         itens=["Previsto × real de todas as rodadas no site.",
                                "Times de especialistas entram só agregados, sem nome.",
                                "Próxima escalação sai antes do fechamento do mercado."]),
         f"Chamada para o diário em {config.DOMINIO}."),
    ])
    texto = legenda(
        f"Rodada {n}: o time do modelo fez {num(real)} pontos. A projeção era {num(proj)} ({sinal(saldo)}).",
        f"Melhor: {melhor['apelido']} ({num(melhor['pontos'], 1)}). Pior: {pior['apelido']} ({num(pior['pontos'], 1)}). "
        f"Capitão {cap['apelido']}: {num(cap['pontos'], 1)} pontos, {num(cap['pontos'] * 1.5, 1) if cap['pontos'] is not None else '–'} com o 1,5×.",
        (f"Entre {len(sp)} times de especialistas que acompanhamos, a mediana foi {num(statistics.median(sp))}." if sp else ""),
        f"Todas as rodadas, previsto × real, em {config.DOMINIO} (link na bio).",
        f"Quanto seu time fez? {config.HASHTAGS}",
    )
    return {
        "pauta": "previsto-real", "slides": slides, "legenda": texto,
        "agendado_para": opcoes.get("quando") or proximo(12),
        "expira_em": None,
        "origem": {"estado": d["estado"], "pontuado_em_utc": d["pontuado_em_utc"], "commit_modelo": d["modelo"]["commit"]},
    }
