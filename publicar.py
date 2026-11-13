"""Publica os posts da fila que já estão no horário. Roda no GitHub Actions.

  IG_TOKEN=... python publicar.py            # publica
  python publicar.py --simular               # só mostra o que publicaria

As imagens vão por URL pública do próprio repositório (raw.githubusercontent.com),
fixada no commit em execução para não pegar cache velho.
"""
import argparse
import json
import os
import sys
import traceback

from ig import config, fila
from ig.api import ErroIG, Instagram
from ig.pautas.comum import agora

MAX_POR_EXECUCAO = 2
MAX_TENTATIVAS = 3


def url_base():
    repo = os.environ.get("GITHUB_REPOSITORY")
    ref = os.environ.get("GITHUB_SHA", "main")
    if not repo:
        sys.exit("defina GITHUB_REPOSITORY (dono/repo) para montar as URLs das imagens")
    return f"https://raw.githubusercontent.com/{repo}/{ref}/fila"


def tentativas(post):
    p = post["_pasta"] / "erro.json"
    return json.loads(p.read_text())["tentativas"] if p.exists() else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()

    now = agora()
    for p in fila.todos():
        exp = fila.quando(p, "expira_em")
        if not p["_publicado"] and exp and now >= exp and not (p["_pasta"] / "expirado").exists():
            print(f"{p['id']}: expirou em {exp:%d/%m %H:%M} sem publicar")
            if not a.simular:
                (p["_pasta"] / "expirado").touch()

    fila_ok = [p for p in fila.pendentes(now) if tentativas(p) < MAX_TENTATIVAS]
    if not fila_ok:
        print("nada para publicar")
        return
    if a.simular:
        for p in fila_ok:
            print(f"publicaria {p['id']} ({len(p['imagens'])} imagens), agendado {p['agendado_para']}")
        return

    if not os.environ.get("IG_TOKEN"):
        sys.exit("IG_TOKEN não configurado: há posts no horário e não dá para publicar")
    ig = Instagram(os.environ["IG_TOKEN"])
    base = url_base()
    falhou = False
    for p in fila_ok[:MAX_POR_EXECUCAO]:
        urls = [f"{base}/{p['id']}/{img}" for img in p["imagens"]]
        try:
            info = ig.publicar(urls, p["legenda"], p.get("alt_text"))
        except (ErroIG, Exception) as e:
            falhou = True
            n = tentativas(p) + 1
            fila.gravar_json(p["_pasta"], "erro.json", {"tentativas": n, "quando": now.isoformat(), "erro": str(e),
                                                        "trace": traceback.format_exc()[-2000:]})
            print(f"{p['id']}: falhou (tentativa {n}/{MAX_TENTATIVAS}): {e}")
            continue
        fila.gravar_json(p["_pasta"], "publicado.json", {
            "media_id": info["id"], "permalink": info.get("permalink"), "publicado_em": agora().isoformat(),
            "timestamp_ig": info.get("timestamp"), "urls": urls,
        })
        (p["_pasta"] / "erro.json").unlink(missing_ok=True)
        print(f"{p['id']}: publicado {info.get('permalink')}")
    if len(fila_ok) > MAX_POR_EXECUCAO:
        print(f"{len(fila_ok) - MAX_POR_EXECUCAO} post(s) ficam para a próxima execução")
    if falhou:
        sys.exit(1)


if __name__ == "__main__":
    main()
