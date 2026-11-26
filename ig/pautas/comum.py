from datetime import datetime, timedelta

from .. import config, fonte


def agora():
    return datetime.now(config.FUSO).replace(second=0, microsecond=0)


def proximo(hora, minuto=0, dias=0):
    """Próximo horário HH:MM em Brasília, a partir de agora, mais `dias`."""
    base = agora()
    alvo = base.replace(hour=hora, minute=minuto) + timedelta(days=dias)
    if alvo <= base:
        alvo += timedelta(days=1)
    return alvo


def apos_fechamento(fecha, opcoes, atraso=timedelta(0)):
    """Posts pré só saem com o mercado fechado: no fechamento (mais o atraso) ou agora, o que vier depois."""
    if opcoes.get("quando"):
        return opcoes["quando"]
    if fecha is None:
        raise fonte.ErroFonte("sem horário de fechamento em pre/status.json; use --quando")
    return max(agora(), fecha + atraso)


def ctx(d, **extra):
    return {"temporada": d["temporada"], "rodada": d["rodada"], **extra}


def numerar(slides):
    total = len(slides)
    for i, (_, c, _) in enumerate(slides, 1):
        c["pagina"], c["paginas"] = i, total
    return slides


def legenda(*blocos):
    texto = "\n\n".join(b.strip() for b in blocos if b and b.strip())
    if "—" in texto:
        raise ValueError("legenda com travessão")
    return texto
