"""Números no formato brasileiro. Ausência vira o marcador do site."""
VAZIO = "–"


def num(v, casas=2):
    if v is None:
        return VAZIO
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def sinal(v, casas=2):
    if v is None:
        return VAZIO
    return ("+" if v > 0 else "") + num(v, casas)


def cartoletas(v):
    return VAZIO if v is None else f"C$ {num(v)}"


MANDO = {"casa": "em casa", "fora": "fora", None: ""}
POSICAO = {"GOL": "Goleiro", "LAT": "Laterais", "ZAG": "Zagueiros", "MEI": "Meias", "ATA": "Atacantes", "TEC": "Técnico"}
POSICAO_PLURAL = {"GOL": "Goleiros", "LAT": "Laterais", "ZAG": "Zagueiros", "MEI": "Meias", "ATA": "Atacantes", "TEC": "Técnicos"}
