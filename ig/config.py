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

# "unificado": login unificado da Meta (padrão desde out/2026). Token de sistema do portfólio
#   empresarial, API em graph.facebook.com.
# "instagram": API com login do Instagram (legado), token de usuário em graph.instagram.com.
# Sem IG_LOGIN, decide pelo token: os do login do Instagram começam com "IG", os da Meta com "EA".
IG_LOGIN = os.environ.get("IG_LOGIN") or ("instagram" if os.environ.get("IG_TOKEN", "").startswith("IG") else "unificado")
IG_HOST = "https://graph.facebook.com" if IG_LOGIN == "unificado" else "https://graph.instagram.com"
IG_VERSAO = os.environ.get("IG_VERSAO", "v27.0")
IG_USER_ID = os.environ.get("IG_USER_ID")  # opcional; sem ele, descobre pela API

LARGURA, ALTURA = 1080, 1350  # 4:5, o maior formato vertical do feed

HASHTAGS = "#CartolaFC #Cartola #Brasileirao #FantasyFootball #DataScience"
