"""Gera os posts de uma rodada na fila (fila/<id>/).

  python gerar.py pre                      # time do modelo (carrossel e story) e raio-x da rodada mais recente
  python gerar.py pos                      # previsto x real (carrossel, story e reel) e temporada
  python gerar.py time-modelo --rodada 34  # uma pauta só
  python gerar.py pos --pr                 # gera, commita numa branch e abre o PR de aprovação
  python gerar.py pre --quando "2026-11-14 12:00"

O merge do PR em main é a aprovação. O GitHub Actions publica no horário.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from ig import config, fila, fonte, render, video
from ig.pautas import PAUTAS, POS, PRE
from ig.pautas.comum import agora


def _renderizar(spec, p):
    """Grava as mídias do post em p e devolve os campos de post.json que dependem do formato."""
    formato = spec.get("formato")
    if formato == "reel":
        with tempfile.TemporaryDirectory() as tmp:
            cenas = []
            for i, (tpl, c, segundos, fundir) in enumerate(spec["cenas"], 1):
                cenas.append((render.slide(tpl, Path(tmp) / f"{i:02d}.jpg", reel=True, **c), segundos, fundir))
            duracao = video.compor(cenas, p / "video.mp4")
        tpl, c = spec["capa"]
        render.slide(tpl, p / "capa.jpg", reel=True, **c)
        if not 3 <= duracao <= 15 * 60:
            raise ValueError(f"reel com {duracao:.1f} s; a API aceita de 3 s a 15 min")
        return {"formato": "reel", "video": "video.mp4", "capa": "capa.jpg", "duracao_s": round(duracao, 1),
                "imagens": ["capa.jpg"], "alt_text": []}
    vertical = formato == "story"
    if vertical and len(spec["slides"]) != 1:
        raise ValueError("story é uma mídia só; para uma sequência, crie uma pauta por story")
    imagens, alts = [], []
    for i, (tpl, c, alt) in enumerate(spec["slides"], 1):
        nome_img = f"{i:02d}.jpg"
        render.slide(tpl, p / nome_img, vertical=vertical, **c)
        imagens.append(nome_img)
        alts.append(alt)
    return {"formato": formato or ("carrossel" if len(imagens) > 1 else "imagem"), "imagens": imagens, "alt_text": alts}


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
    midia = _renderizar(spec, p)
    ag, exp = spec["agendado_para"], spec.get("expira_em")
    if exp and ag >= exp:
        print(f"  aviso: {post_id} agendado para depois de expirar ({exp:%d/%m %H:%M}); não vai ser publicado")
    fila.gravar_json(p, "post.json", {
        "id": post_id, "pauta": spec["pauta"], "temporada": t, "rodada": n, **midia,
        "agendado_para": ag.isoformat(), "expira_em": exp.isoformat() if exp else None,
        "legenda": spec["legenda"], "gerado_em": agora().isoformat(), "origem": spec.get("origem", {}),
        "depende_de": f"{t}-{n:02d}-{spec['depende_de']}" if spec.get("depende_de") else None,
    })
    if spec["legenda"]:
        (p / "legenda.txt").write_text(spec["legenda"] + "\n", encoding="utf-8")
    resumo = (f"reel de {midia['duracao_s']} s" if midia["formato"] == "reel"
              else f"{midia['formato']}, {len(midia['imagens'])} imagem(ns)")
    print(f"  {post_id}: {resumo}, publica a partir de {ag:%d/%m %H:%M}"
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
            raw = f"https://raw.githubusercontent.com/{repo}/{branch}/fila/{i}"
            fmt = post.get("formato", "carrossel")
            corpo.append(f"## {i} ({fmt})\n\nPublica a partir de **{post['agendado_para']}**"
                         + (f", expira {post['expira_em']}" if post["expira_em"] else "") + "\n")
            corpo.append(" ".join(f'<img src="{raw}/{img}" width="260">' for img in post["imagens"]))
            if fmt == "reel":
                corpo.append(f"\nCapa acima. [Assistir ao vídeo ({post['duracao_s']} s)]({raw}/{post['video']})\n")
            if post["legenda"]:
                corpo.append("\n<details><summary>Legenda</summary>\n\n```\n" + post["legenda"] + "\n```\n</details>\n")
            elif fmt == "story":
                corpo.append("\nStory não tem legenda.\n")
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
