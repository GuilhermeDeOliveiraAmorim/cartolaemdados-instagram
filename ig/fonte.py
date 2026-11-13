"""Leitura dos dados do cartola-dados.

A fonte principal é o JSON do diário (contrato v1 do site), gerado na hora pelo
exportar_diario.py do cartola-dados. Assim o post mostra exatamente o que o site
mostra. Notas e média do Cartola vêm do arquivo publicado no site, se existir.
"""
import csv
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from . import config


class ErroFonte(Exception):
    pass


def _python_dados():
    venv = config.CARTOLA_DADOS / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else "python3"


def _publicado_no_site(t, n):
    nome = f"content/rodadas/{t}-{n:02d}.json"
    r = subprocess.run(["git", "-C", str(config.SITE), "show", f"origin/master:{nome}"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return r.stdout
    local = config.SITE / nome
    return local.read_text(encoding="utf-8") if local.exists() else None


def diario(t, n, media_cartola=None):
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / f"{t}-{n:02d}.json"
        site = _publicado_no_site(t, n)
        if site:
            destino.write_text(site, encoding="utf-8")
        cmd = [_python_dados(), "exportar_diario.py", "--temporada", str(t), "--rodada", str(n), "--saida", tmp]
        if media_cartola is not None:
            cmd += ["--media-cartola", str(media_cartola)]
        r = subprocess.run(cmd, cwd=config.CARTOLA_DADOS, capture_output=True, text=True)
        if r.returncode != 0:
            raise ErroFonte(f"exportar_diario.py falhou na rodada {n}:\n{r.stdout}{r.stderr}")
        return json.loads(destino.read_text(encoding="utf-8"))


def pasta_rodada(t, n):
    return config.CARTOLA_DADOS / "dados_api" / str(t) / f"rodada-{n}"


def rodadas_com_modelo(t):
    base = config.CARTOLA_DADOS / "dados_api" / str(t)
    ns = [int(p.name.split("-")[1]) for p in base.glob("rodada-*") if (p / "modelo").is_dir()]
    return sorted(ns)


def ultima_rodada(t):
    ns = rodadas_com_modelo(t)
    if not ns:
        raise ErroFonte(f"nenhuma rodada com modelo/ em {t}")
    return ns[-1]


def _float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def projecoes(t, n):
    """Candidatos da execução mais recente do modelo, ordenados pela projeção."""
    execs = sorted(p for p in (pasta_rodada(t, n) / "modelo").iterdir() if p.is_dir())
    if not execs:
        raise ErroFonte(f"rodada {n} sem execução em modelo/")
    with open(execs[-1] / "projecoes.csv", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    out = []
    for r in linhas:
        mando = _float(r.get("mando"))
        out.append({
            "atleta_id": int(r["atleta_id"]), "posicao": r["posicao"], "apelido": r["apelido"],
            "clube": r["clube"], "adversario": r.get("adv") or None,
            "mando": None if mando is None else ("casa" if mando == 1 else "fora"),
            "preco": _float(r.get("preco_mercado")), "proj": _float(r.get("proj")), "teto": _float(r.get("teto")),
        })
    return sorted(out, key=lambda a: -(a["proj"] or -99))


def fechamento(t, n):
    """Horário de fechamento do mercado (fuso de Brasília) ou None."""
    p = pasta_rodada(t, n) / "pre" / "status.json"
    if not p.exists():
        return None
    f = json.loads(p.read_text(encoding="utf-8")).get("fechamento") or {}
    try:
        return datetime(f["ano"], f["mes"], f["dia"], f["hora"], f["minuto"], tzinfo=config.FUSO)
    except KeyError:
        return None
