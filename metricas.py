"""Coleta métricas do Instagram e gera o relatório. Roda no GitHub Actions, uma vez por dia.

  IG_TOKEN=... python metricas.py           # coleta e regrava metricas/RELATORIO.md
  python metricas.py --so-relatorio         # só o relatório, com o que já foi coletado
  IG_TOKEN=... python metricas.py --stories # só stories perto de 24 h (a API apaga as métricas depois)

metricas/posts.csv  uma linha por post e por coleta (a curva de cada post ao longo dos dias)
metricas/conta.csv  uma linha por dia: seguidores e totais da conta no dia anterior
"""
import argparse
import csv
import os
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

from ig import config, fila
from ig.api import ErroIG, Instagram
from ig.formato import num
from ig.pautas.comum import agora

DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
JANELA_DIAS = 30  # depois disso o post quase não muda; para de coletar
STORY_FINAL = (20, 24)  # horas de vida em que o story tem a coleta final, antes de a API apagar as métricas
CAMPOS_POST = ["coletado_em", "post_id", "pauta", "formato", "temporada", "rodada", "media_id", "publicado_em", "horas",
               "like_count", "comments_count", *Instagram.METRICAS_POST]
CAMPOS_CONTA = ["data", "seguidores", "seguindo", "posts", "reach", "views", "profile_views", "accounts_engaged",
                "total_interactions", "website_clicks", "seguiu", "deixou"]

ARQ_POSTS = config.METRICAS / "posts.csv"
ARQ_CONTA = config.METRICAS / "conta.csv"


def ler_csv(p):
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def anexar(p, campos, linhas):
    if not linhas:
        return
    p.parent.mkdir(exist_ok=True)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            cabecalho = next(csv.reader(f), [])
        if cabecalho != campos:  # coluna nova: regrava o histórico com o cabeçalho novo
            antigas = ler_csv(p)
            with open(p, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
                w.writeheader()
                w.writerows(antigas)
    novo = not p.exists()
    with open(p, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if novo:
            w.writeheader()
        w.writerows(linhas)


def formato(post):
    return post.get("formato", "carrossel")


def coletar(ig, so_stories=False):
    now = agora()
    ja_final = {r["post_id"] for r in ler_csv(ARQ_POSTS) if (_f(r.get("horas")) or 0) >= STORY_FINAL[0]}
    linhas = []
    for p in fila.todos():
        pub = p["_publicado"]
        if not pub:
            continue
        fmt = formato(p)
        horas = (now - datetime.fromisoformat(pub["publicado_em"])).total_seconds() / 3600
        if fmt == "story":
            if horas >= 24:
                continue  # a API não devolve mais nada
            if so_stories and (horas < STORY_FINAL[0] or p["id"] in ja_final):
                continue
        elif so_stories or horas > JANELA_DIAS * 24:
            continue
        try:
            m = ig.insights_post(pub["media_id"], fmt)
            c = ig.campos_post(pub["media_id"], fmt)
        except ErroIG as e:
            print(f"{p['id']}: {e}")
            continue
        linhas.append({"coletado_em": now.isoformat(), "post_id": p["id"], "pauta": p["pauta"], "formato": fmt,
                       "temporada": p["temporada"], "rodada": p["rodada"], "media_id": pub["media_id"],
                       "publicado_em": pub["publicado_em"], "horas": round(horas, 1),
                       "like_count": c.get("like_count"), "comments_count": c.get("comments_count"), **m})
    anexar(ARQ_POSTS, CAMPOS_POST, linhas)
    print(f"{len(linhas)} post(s) coletados")
    if so_stories:
        return bool(linhas)

    ontem = (now - timedelta(days=1)).date()
    if any(r["data"] == ontem.isoformat() for r in ler_csv(ARQ_CONTA)):
        return True
    eu = ig.eu()
    ini = datetime.combine(ontem, datetime.min.time(), config.FUSO)
    conta = ig.insights_conta(ini.timestamp(), (ini + timedelta(days=1)).timestamp())
    anexar(ARQ_CONTA, CAMPOS_CONTA, [{"data": ontem.isoformat(), "seguidores": eu.get("followers_count"),
                                      "seguindo": eu.get("follows_count"), "posts": eu.get("media_count"), **conta}])
    print(f"conta: {eu.get('followers_count')} seguidores")
    return True


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pct(v):
    return "–" if v is None else f"{num(v * 100, 1)}%"


def relatorio():
    posts = ler_csv(ARQ_POSTS)
    conta = ler_csv(ARQ_CONTA)
    ultimo = {}
    for r in posts:
        ultimo[r["post_id"]] = r  # o CSV é cronológico: fica a coleta mais recente
    linhas = ["# Relatório do Instagram", "", f"Gerado em {agora():%d/%m/%Y %H:%M} (Brasília). "
              "Métricas da coleta mais recente de cada post. Taxas sobre o alcance.", ""]

    if conta:
        c0, c1 = conta[0], conta[-1]
        linhas += ["## Conta", "", f"- Seguidores: **{c1['seguidores']}** em {c1['data']} "
                   f"({int(_f(c1['seguidores']) - _f(c0['seguidores'])):+d} desde {c0['data']})."]
        ult7 = conta[-7:]
        for campo, nome in [("reach", "Alcance"), ("profile_views", "Visitas ao perfil"), ("website_clicks", "Cliques no link")]:
            vals = [_f(r[campo]) for r in ult7 if _f(r[campo]) is not None]
            if vals:
                linhas.append(f"- {nome}, últimos {len(vals)} dias: {int(sum(vals))}.")
        linhas.append("")

    if not ultimo:
        linhas += ["Nenhum post publicado ainda."]
    else:
        linhas += ["## Posts", "", "| Post | Formato | Publicado | Alcance | Curtidas | Coment. | Salvos | Compart. | Seguiu | Interação/alcance |",
                   "|---|---|---|--:|--:|--:|--:|--:|--:|--:|"]
        for r in sorted(ultimo.values(), key=lambda r: r["publicado_em"], reverse=True):
            alc, inter = _f(r["reach"]), _f(r["total_interactions"])
            taxa = f"{num(inter / alc * 100, 1)}%" if alc and inter is not None else "–"
            pub = datetime.fromisoformat(r["publicado_em"])
            linhas.append(f"| {r['post_id']} | {r.get('formato') or 'carrossel'} | {pub:%d/%m} {DIAS[pub.weekday()]} {pub:%H:%M} | {r['reach'] or '–'} | {r['like_count'] or '–'} | "
                          f"{r['comments_count'] or '–'} | {r['saved'] or '–'} | {r['shares'] or '–'} | {r['follows'] or '–'} | {taxa} |")

        por_pauta = defaultdict(list)
        for r in ultimo.values():
            por_pauta[r["pauta"]].append(r)
        linhas += ["", "## Por pauta", "", "| Pauta | Posts | Alcance médio | Salvos/alcance | Compart./alcance | Seguiu por post |",
                   "|---|--:|--:|--:|--:|--:|"]

        def media(rs, campo, base=None):
            vals = []
            for r in rs:
                v, b = _f(r[campo]), _f(r[base]) if base else 1
                if v is not None and b:
                    vals.append(v / b)
            return statistics.mean(vals) if vals else None

        geral = media(ultimo.values(), "reach")
        alertas = []
        for pauta, rs in sorted(por_pauta.items()):
            alc = media(rs, "reach")
            sv, sh = media(rs, "saved", "reach"), media(rs, "shares", "reach")
            linhas.append(f"| {pauta} | {len(rs)} | {num(alc, 0)} | {pct(sv)} | {pct(sh)} | {num(media(rs, 'follows'), 1)} |")
            if len(rs) >= 3 and alc is not None and geral and alc < 0.6 * geral:
                alertas.append(f"- **{pauta}** alcança {num(alc / geral * 100, 0)}% da média geral em {len(rs)} posts: rever formato ou horário.")
        video = [r for r in ultimo.values() if r.get("formato") in ("reel", "story")]
        if video:
            linhas += ["", "## Reels e stories", "",
                       "Story só tem métrica nas primeiras 24 h; o número é o da última coleta antes disso.", "",
                       "| Post | Formato | Horas | Views | Tempo médio assistido | Taxa de pulo | Respostas |", "|---|---|--:|--:|--:|--:|--:|"]
            for r in sorted(video, key=lambda r: r["publicado_em"], reverse=True):
                tempo = _f(r.get("ig_reels_avg_watch_time"))
                pulo = _f(r.get("reels_skip_rate"))
                linhas.append(f"| {r['post_id']} | {r['formato']} | {num(_f(r['horas']), 0)} | {r['views'] or '–'} | "
                              f"{num(tempo / 1000, 1) + ' s' if tempo is not None else '–'} | "
                              f"{num(pulo, 1) + '%' if pulo is not None else '–'} | {r.get('replies') or '–'} |")
        if alertas:
            linhas += ["", "## Para olhar", "", *alertas]
        if len(ultimo) < 10:
            linhas += ["", f"_Com {len(ultimo)} post(s), as médias por pauta ainda são ruído. Vale comparar a partir de uns 10._"]
    (config.METRICAS / "RELATORIO.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("metricas/RELATORIO.md atualizado")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-relatorio", action="store_true")
    ap.add_argument("--stories", action="store_true", help="só a coleta final dos stories perto de 24 h")
    a = ap.parse_args()
    if not a.so_relatorio:
        if not os.environ.get("IG_TOKEN"):
            print("IG_TOKEN não configurado; nada a coletar")
            return
        if not coletar(Instagram(os.environ["IG_TOKEN"]), a.stories):
            return
    relatorio()


if __name__ == "__main__":
    main()
