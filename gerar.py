"""Gera os posts de uma rodada na fila (fila/<id>/).

  python gerar.py pre                      # raio-x e time do modelo da rodada mais recente
  python gerar.py pos                      # previsto x real e temporada da rodada mais recente
  python gerar.py time-modelo --rodada 34  # uma pauta só
  python gerar.py pos --pr                 # gera, commita numa branch e abre o PR de aprovação
  python gerar.py pre --quando "2026-11-14 12:00"

O merge do PR em main é a aprovação. O GitHub Actions publica no horário.
"""
import argparse
import shutil
import subprocess
import sys
from datetime import datetime

from ig import config, fila, fonte, render
from ig.pautas import PAUTAS, POS, PRE
from ig.pautas.comum import agora


def gerar_post(nome, t, n, opcoes):
    spec = PAUTAS[nome].montar(t, n, opcoes)
    post_id = f"{t}-{n:02d}-{spec['pauta']}"
    p = fila.pasta(post_id)
    if (p / "publicado.json").exists():
        print(f"  {post_id}: já publicado, não regero")
        return None
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    imagens, alts = [], []
    for i, (tpl, c, alt) in enumerate(spec["slides"], 1):
        nome_img = f"{i:02d}.jpg"
        render.slide(tpl, p / nome_img, **c)
        imagens.append(nome_img)
        alts.append(alt)
    ag, exp = spec["agendado_para"], spec.get("expira_em")
    if exp and ag >= exp:
        print(f"  aviso: {post_id} agendado para depois de expirar ({exp:%d/%m %H:%M}); não vai ser publicado")
    fila.gravar_json(p, "post.json", {
        "id": post_id, "pauta": spec["pauta"], "temporada": t, "rodada": n,
        "formato": "carrossel" if len(imagens) > 1 else "imagem",
        "agendado_para": ag.isoformat(), "expira_em": exp.isoformat() if exp else None,
        "imagens": imagens, "alt_text": alts, "legenda": spec["legenda"],
        "gerado_em": agora().isoformat(), "origem": spec.get("origem", {}),
    })
    (p / "legenda.txt").write_text(spec["legenda"] + "\n", encoding="utf-8")
    print(f"  {post_id}: {len(imagens)} imagem(ns), publica a partir de {ag:%d/%m %H:%M}"
          + (f", expira {exp:%d/%m %H:%M}" if exp else ""))
    return post_id


def git(*args, **kw):
    return subprocess.run(["git", *args], cwd=config.RAIZ, check=True, text=True, capture_output=True, **kw).stdout.strip()


def abrir_pr(ids, t, n, momento):
    repo = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                          cwd=config.RAIZ, check=True, text=True, capture_output=True).stdout.strip()
    branch = f"post/{t}-{n:02d}-{momento}-{datetime.now():%H%M}"
    base = git("rev-parse", "--abbrev-ref", "HEAD")
    git("switch", "-c", branch)
    try:
        git("add", *[f"fila/{i}" for i in ids])
        git("commit", "-m", f"chore(fila): posts da rodada {n} ({momento})")
        git("push", "-u", "origin", branch)
        corpo = []
        for i in ids:
            post = fila.ler(fila.pasta(i))
            corpo.append(f"## {i}\n\nPublica a partir de **{post['agendado_para']}**"
                         + (f", expira {post['expira_em']}" if post["expira_em"] else "") + "\n")
            corpo.append(" ".join(f'<img src="https://raw.githubusercontent.com/{repo}/{branch}/fila/{i}/{img}" width="260">'
                                  for img in post["imagens"]))
            corpo.append("\n<details><summary>Legenda</summary>\n\n```\n" + post["legenda"] + "\n```\n</details>\n")
        corpo.append("Merge = aprovação. O Actions publica no horário agendado.")
        url = subprocess.run(["gh", "pr", "create", "--base", "main", "--head", branch,
                              "--title", f"Posts da rodada {n} ({momento})", "--body", "\n".join(corpo)],
                             cwd=config.RAIZ, check=True, text=True, capture_output=True).stdout.strip()
        print(url)
    finally:
        git("switch", base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("o_que", help="pre, pos ou o nome de uma pauta: " + ", ".join(PAUTAS))
    ap.add_argument("--temporada", type=int, default=datetime.now().year)
    ap.add_argument("--rodada", type=int)
    ap.add_argument("--quando", help="horário de Brasília, AAAA-MM-DD HH:MM (padrão: o de cada pauta)")
    ap.add_argument("--media-cartola", type=float, help="média do Cartola na rodada (aparece no app)")
    ap.add_argument("--forcar", action="store_true", help="gera mesmo fora do momento certo (para teste)")
    ap.add_argument("--pr", action="store_true", help="commita numa branch e abre o PR de aprovação")
    a = ap.parse_args()

    nomes = PRE if a.o_que == "pre" else POS if a.o_que == "pos" else [a.o_que]
    if any(x not in PAUTAS for x in nomes):
        sys.exit(f"pauta desconhecida: {a.o_que}")
    n = a.rodada or fonte.ultima_rodada(a.temporada)
    opcoes = {"forcar": a.forcar, "media_cartola": a.media_cartola,
              "quando": datetime.strptime(a.quando, "%Y-%m-%d %H:%M").replace(tzinfo=config.FUSO) if a.quando else None}
    print(f"rodada {n} de {a.temporada}")
    ids = []
    for nome in nomes:
        try:
            pid = gerar_post(nome, a.temporada, n, opcoes)
        except fonte.ErroFonte as e:
            print(f"  {nome}: {e}")
            continue
        if pid:
            ids.append(pid)
    if a.pr and ids:
        abrir_pr(ids, a.temporada, n, a.o_que)


if __name__ == "__main__":
    main()
