"""Pré-rodada: as maiores projeções do modelo por posição (todos os prováveis, não só o time)."""
from datetime import timedelta

from .. import config, fonte
from ..formato import POSICAO_PLURAL, num
from .comum import agora, ctx, legenda, numerar

POSICOES = ["GOL", "LAT", "ZAG", "MEI", "ATA", "TEC"]
TOP = 5


def montar(t, n, opcoes):
    d = fonte.diario(t, n)
    if d["estado"] != "aberta" and not opcoes.get("forcar"):
        raise fonte.ErroFonte(f"rodada {n} já está fechada; o raio-x é post de antes do fechamento")
    proj = [a for a in fonte.projecoes(t, n) if a["proj"] is not None]
    no_time = {a["atleta_id"] for a in d["atletas"] if a["papel"] == "titular"}
    por_pos = {p: [dict(a, no_time=a["atleta_id"] in no_time) for a in proj if a["posicao"] == p][:TOP] for p in POSICOES}
    lideres = [por_pos[p][0] for p in POSICOES if por_pos[p]]

    slides = [("capa_raiox.html", ctx(d, lideres=lideres, candidatos=len(proj)),
               f"Capa do Raio-X da rodada {n}: maior projeção por posição. "
               + "; ".join(f"{l['posicao']} {l['apelido']} {num(l['proj'])}" for l in lideres) + ".")]
    for p in POSICOES:
        itens = por_pos[p]
        if not itens:
            continue
        escala = max((a["teto"] or a["proj"]) for a in itens) * 1.15
        slides.append(("posicao.html", ctx(d, posicao=p, itens=itens, escala=escala),
                       f"{POSICAO_PLURAL[p]} com maior projeção: "
                       + "; ".join(f"{a['apelido']} ({a['clube']}) projeção {num(a['proj'])}, teto {num(a['teto'], 1)}" for a in itens) + "."))
    slides.append(("cta.html", ctx(d, chapeu="Como ler", titulo="Projeção e teto",
                                   texto="Projeção é a média esperada. Teto é o que o jogador faz num cenário bom: quanto maior a distância, mais imprevisível.",
                                   itens=["O modelo considera adversário, mando, forma recente, xG e preço.",
                                          "\"No time\" marca quem está na escalação do modelo.",
                                          "O time completo sai no próximo post e no site."]),
                   f"Explicação de projeção e teto, e chamada para {config.DOMINIO}."))
    numerar(slides)

    texto = legenda(
        f"Raio-X da rodada {n}: quem o modelo mais projeta em cada posição.",
        "\n".join(f"{p}: {por_pos[p][0]['apelido']} ({num(por_pos[p][0]['proj'])})" for p in POSICOES if por_pos[p]),
        "Projeção é a média esperada; o traço cinza é o teto, um cenário bom. Quanto mais longe o teto, mais imprevisível.",
        f"Escalação completa do modelo em {config.DOMINIO} (link na bio).",
        f"Salva para consultar na hora de escalar. {config.HASHTAGS}",
    )
    fecha = fonte.fechamento(t, n)
    return {
        "pauta": "raio-x", "slides": slides, "legenda": texto,
        "agendado_para": opcoes.get("quando") or agora(),
        "expira_em": fecha - timedelta(minutes=10) if fecha else None,
        "origem": {"estado": d["estado"], "escalado_em_utc": d["escalado_em_utc"], "commit_modelo": d["modelo"]["commit"]},
    }
