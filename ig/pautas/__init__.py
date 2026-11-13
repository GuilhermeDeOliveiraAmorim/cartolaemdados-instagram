"""Cada pauta monta um post a partir dos dados de uma rodada.

montar(temporada, rodada, opcoes) devolve um dict com:
  pauta, slides [(template, contexto, alt_text)], legenda, agendado_para, expira_em, origem
"""
from . import previsto_real, raio_x, temporada, time_modelo

PAUTAS = {
    "time-modelo": time_modelo,
    "raio-x": raio_x,
    "previsto-real": previsto_real,
    "temporada": temporada,
}
# O que gerar em cada momento da rodada.
PRE = ["raio-x", "time-modelo"]
POS = ["previsto-real", "temporada"]
