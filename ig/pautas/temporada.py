"""Pós-rodada: o acumulado da temporada, previsto × real em cada rodada registrada ao vivo."""
import statistics

from .. import config, fonte
from ..formato import num, sinal
from .comum import ctx, legenda, numerar, proximo
from .previsto_real import escala, sugeridos_pontos


def montar(t, n, opcoes):
    fechadas = []
    for r in fonte.rodadas_com_modelo(t):
        if r > n:
            continue
        d = fonte.diario(t, r, opcoes.get("media_cartola") if r == n else None)
        if d["estado"] == "fechada" and d["resultado"]["pontos"] is not None:
            fechadas.append(d)
    if len(fechadas) < 2:
        raise fonte.ErroFonte("menos de 2 rodadas fechadas com registro ao vivo; o acumulado fica para depois")

    real = [d["resultado"]["pontos"] for d in fechadas]
    proj = [d["time"]["projecao"] for d in fechadas]
    acima = sum(r > p for r, p in zip(real, proj))
    vs_med = [(d["resultado"]["pontos"], statistics.median(sp)) for d in fechadas if (sp := sugeridos_pontos(d))]
    venceu_med = sum(r > m for r, m in vs_med)
    ultima = fechadas[-1]

    itens = [{"rotulo": f"R{d['rodada']}", "nome": sinal(d["resultado"]["pontos"] - d["time"]["projecao"], 1),
              "capitao": False, "prev": d["time"]["projecao"], "real": d["resultado"]["pontos"]} for d in fechadas]
    x = escala([v for i in itens for v in (i["prev"], i["real"])])

    cartoes = [
        {"etiqueta": "Rodadas", "nome": "Registradas ao vivo", "linha": "time publicado antes do fechamento",
         "valor": str(len(fechadas))},
        {"etiqueta": "Média por rodada", "nome": "Pontos reais", "linha": f"projeção média {num(statistics.mean(proj))}",
         "valor": num(statistics.mean(real), 1), "sub": sinal(statistics.mean(real) - statistics.mean(proj), 1)},
        {"etiqueta": "Projeção", "nome": "Rodadas acima", "linha": "o time fez mais que o previsto",
         "valor": f"{acima}/{len(fechadas)}"},
    ]
    if vs_med:
        cartoes.append({"etiqueta": "Especialistas", "nome": "Acima da mediana", "linha": "dos times acompanhados na rodada",
                        "valor": f"{venceu_med}/{len(vs_med)}"})

    slides = numerar([
        ("cartoes.html", ctx(ultima, chapeu=f"Temporada {t} · até a rodada {ultima['rodada']}", titulo="O modelo na temporada", cartoes=cartoes),
         f"Resumo da temporada: {len(fechadas)} rodadas registradas, média real {num(statistics.mean(real), 1)} contra "
         f"{num(statistics.mean(proj), 1)} projetados, {acima} rodadas acima da projeção."),
        ("halteres.html", ctx(ultima, chapeu="Rodada a rodada", titulo="Previsto × real", itens=itens, x=x,
                              nota_legenda="total do time · saldo ao lado", rodape_texto="Só rodadas com o time registrado antes do fechamento."),
         "Gráfico por rodada: " + "; ".join(f"rodada {d['rodada']}: previsto {num(p, 1)}, real {num(r, 1)}"
                                            for d, p, r in zip(fechadas, proj, real)) + "."),
        ("cta.html", ctx(ultima, chapeu="Transparência", titulo="Nenhuma rodada some",
                         texto="Cada escalação fica registrada com data, hora e versão do modelo antes de a bola rolar.",
                         itens=["Diário completo no site.", "Backtest de 2023 a 2026 na página do modelo.",
                                "Experimentos aceitos e rejeitados no laboratório."]),
         f"Chamada para {config.DOMINIO}."),
    ])
    texto = legenda(
        f"O modelo na temporada {t}, até a rodada {ultima['rodada']}: média de {num(statistics.mean(real), 1)} pontos por rodada "
        f"contra {num(statistics.mean(proj), 1)} projetados.",
        f"Fez mais que a projeção em {acima} de {len(fechadas)} rodadas."
        + (f" Superou a mediana dos times de especialistas acompanhados em {venceu_med} de {len(vs_med)}." if vs_med else ""),
        "Só contam rodadas em que o time foi registrado antes do fechamento do mercado.",
        f"Detalhes em {config.DOMINIO} (link na bio). {config.HASHTAGS}",
    )
    return {
        "pauta": "temporada", "slides": slides, "legenda": texto,
        "agendado_para": opcoes.get("quando") or proximo(18, dias=1),
        "expira_em": None,
        "origem": {"rodadas": [d["rodada"] for d in fechadas]},
    }
