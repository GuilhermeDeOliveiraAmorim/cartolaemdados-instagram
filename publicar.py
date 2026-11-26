"""Publica os posts da fila que já estão no horário. Roda no GitHub Actions.

  IG_TOKEN=... python publicar.py            # publica
  python publicar.py --simular               # só mostra o que publicaria

As imagens vão por URL pública do próprio repositório (raw.githubusercontent.com),
fixada no commit em execução para não pegar cache velho. O vídeo do reel sobe direto do
checkout (upload resumível) no login unificado e por URL no login do Instagram.
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


def enviar(ig, p, base):
    """Publica um post da fila conforme o formato. Devolve (info da API, URLs usadas)."""
    raiz = f"{base}/{p['id']}"
    fmt = p.get("formato", "carrossel")
    if fmt == "reel":
        urls = [f"{raiz}/{p['video']}", f"{raiz}/{p['capa']}"]
        return ig.publicar_reel(p["_pasta"] / p["video"], urls[0], p["legenda"], capa_url=urls[1]), urls
    if fmt == "story":
        if p.get("video"):
            urls = [f"{raiz}/{p['video']}"]
            return ig.publicar_story(arquivo=p["_pasta"] / p["video"], video_url=urls[0]), urls
        urls = [f"{raiz}/{p['imagens'][0]}"]
        return ig.publicar_story(imagem_url=urls[0]), urls
    urls = [f"{raiz}/{img}" for img in p["imagens"]]
    return ig.publicar(urls, p["legenda"], p.get("alt_text")), urls


def descrever(p):
    fmt = p.get("formato", "carrossel")
    return f"reel de {p.get('duracao_s')} s" if fmt == "reel" else f"{fmt}, {len(p['imagens'])} imagem(ns)"


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
            dep = fila.aguardando(p)
            print(f"publicaria {p['id']} ({descrever(p)}), agendado {p['agendado_para']}"
                  + (f", depois de {dep} (ainda não publicado)" if dep else ""))
        return

    if not os.environ.get("IG_TOKEN"):
        sys.exit("IG_TOKEN não configurado: há posts no horário e não dá para publicar")
    ig = Instagram(os.environ["IG_TOKEN"])
    base = url_base()
    falhou = False
    feitos = 0
    for p in fila_ok:
        if feitos == MAX_POR_EXECUCAO:
            print(f"{len(fila_ok) - fila_ok.index(p)} post(s) ficam para a próxima execução")
            break
        dep = fila.aguardando(p)  # relido a cada post: o carrossel pode ter saído nesta mesma execução
        if dep:
            print(f"{p['id']}: aguardando {dep} ser publicado")
            continue
        feitos += 1
        try:
            info, urls = enviar(ig, p, base)
        except (ErroIG, Exception) as e:
            falhou = True
            n = tentativas(p) + 1
            fila.gravar_json(p["_pasta"], "erro.json", {"tentativas": n, "quando": now.isoformat(), "erro": str(e),
                                                        "trace": traceback.format_exc()[-2000:]})
            print(f"{p['id']}: falhou (tentativa {n}/{MAX_TENTATIVAS}): {e}")
            continue
        fila.gravar_json(p["_pasta"], "publicado.json", {
            "media_id": info["id"], "permalink": info.get("permalink"), "publicado_em": agora().isoformat(),
            "timestamp_ig": info.get("timestamp"), "formato": p.get("formato", "carrossel"),
            "tipo_ig": info.get("media_product_type"), "urls": urls,
        })
        (p["_pasta"] / "erro.json").unlink(missing_ok=True)
        print(f"{p['id']}: publicado ({descrever(p)}) {info.get('permalink') or info['id']}")
    if falhou:
        sys.exit(1)


if __name__ == "__main__":
    main()
