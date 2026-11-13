from datetime import datetime, timedelta

from .. import config


def agora():
    return datetime.now(config.FUSO).replace(second=0, microsecond=0)


def proximo(hora, minuto=0, dias=0):
    """Próximo horário HH:MM em Brasília, a partir de agora, mais `dias`."""
    base = agora()
    alvo = base.replace(hour=hora, minute=minuto) + timedelta(days=dias)
    if alvo <= base:
        alvo += timedelta(days=1)
    return alvo


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
