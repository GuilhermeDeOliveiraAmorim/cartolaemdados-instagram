"""Caminhos e constantes. Tudo pode ser trocado por variável de ambiente."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
FILA = RAIZ / "fila"
METRICAS = RAIZ / "metricas"
TEMPLATES = RAIZ / "templates"

CARTOLA_DADOS = Path(os.environ.get("CARTOLA_DADOS", RAIZ.parent / "cartola-dados"))
SITE = Path(os.environ.get("CARTOLA_SITE", RAIZ.parent / "cartola"))
CHROME = os.environ.get("CHROME", "google-chrome")

FUSO = ZoneInfo("America/Sao_Paulo")
DOMINIO = "cartolaemdados.com.br"
PERFIL = "@cartolaemdados"

# Instagram API com login do Instagram (sem Página do Facebook).
IG_HOST = "https://graph.instagram.com"
IG_VERSAO = os.environ.get("IG_VERSAO", "v27.0")

LARGURA, ALTURA = 1080, 1350  # 4:5, o maior formato vertical do feed

HASHTAGS = "#CartolaFC #Cartola #Brasileirao #FantasyFootball #DataScience"
