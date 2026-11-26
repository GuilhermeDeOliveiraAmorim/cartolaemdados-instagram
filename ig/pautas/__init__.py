"""Cada pauta monta um post a partir dos dados de uma rodada.

montar(temporada, rodada, opcoes) devolve um dict com:
  pauta, legenda, agendado_para, expira_em, origem, depende_de (opcional: pauta da mesma rodada que
  precisa estar publicada antes) e, conforme o formato:
  - carrossel ou imagem (padrão): slides [(template, contexto, alt_text)], feed 4:5
  - "formato": "story": slides com um item, 9:16, sem legenda (a API não aceita)
  - "formato": "reel": cenas [(template, contexto, segundos, fundir)] e capa (template, contexto), 9:16
"""
from . import previsto_real, raio_x, reel_previsto_real, story_resultado, story_time, temporada, time_modelo

PAUTAS = {
    "time-modelo": time_modelo,
    "story-time": story_time,
    "raio-x": raio_x,
    "previsto-real": previsto_real,
    "story-resultado": story_resultado,
    "reel-previsto-real": reel_previsto_real,
    "temporada": temporada,
}
# O que gerar em cada momento da rodada.
PRE = ["time-modelo", "story-time", "raio-x"]
POS = ["previsto-real", "story-resultado", "reel-previsto-real", "temporada"]
