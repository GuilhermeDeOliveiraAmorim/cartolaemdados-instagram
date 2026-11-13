"""Fila de posts: uma pasta por post em fila/<id>/.

post.json      o que publicar e quando (gerado localmente, aprovado no merge do PR)
NN.jpg         as imagens, na ordem do carrossel
publicado.json escrito pelo publicador (media_id, permalink, horário)
erro.json      última falha de publicação
"""
import json
from datetime import datetime
from pathlib import Path

from . import config


def pasta(post_id):
    return config.FILA / post_id


def ler(p: Path):
    post = json.loads((p / "post.json").read_text(encoding="utf-8"))
    pub = p / "publicado.json"
    post["_pasta"] = p
    post["_publicado"] = json.loads(pub.read_text(encoding="utf-8")) if pub.exists() else None
    return post


def todos():
    if not config.FILA.exists():
        return []
    return [ler(p) for p in sorted(config.FILA.iterdir()) if (p / "post.json").exists()]


def quando(post, campo):
    v = post.get(campo)
    return datetime.fromisoformat(v) if v else None


def pendentes(agora):
    """Posts não publicados, já no horário e não expirados, mais antigos primeiro."""
    out = []
    for p in todos():
        if p["_publicado"]:
            continue
        exp = quando(p, "expira_em")
        if quando(p, "agendado_para") <= agora and (exp is None or agora < exp):
            out.append(p)
    return sorted(out, key=lambda p: p["agendado_para"])


def gravar_json(p: Path, nome, dados):
    (p / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
