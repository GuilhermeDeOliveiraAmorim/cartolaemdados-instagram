"""Confere o token: conta, seguidores, cota de publicação (24 h) e validade do token.

  IG_TOKEN=... python checar.py
"""
import os
from datetime import datetime

from ig import config
from ig.api import ErroIG, Instagram

token = os.environ["IG_TOKEN"]
ig = Instagram(token)
eu = ig.eu()
print(f"@{eu['username']} (id {eu['user_id']}): {eu.get('followers_count')} seguidores, {eu.get('media_count')} posts")
lim = ig.limite()
print(f"cota de publicação: {lim.get('quota_usage')} usados de {(lim.get('config') or {}).get('quota_total')} em 24 h")
try:
    d = ig._req("GET", "debug_token", input_token=token)["data"]
    exp = d.get("expires_at") or 0
    print("token: " + ("não expira" if exp == 0 else f"expira em {datetime.fromtimestamp(exp):%d/%m/%Y}")
          + f"; permissões: {', '.join(d.get('scopes', []))}")
except ErroIG as e:
    print(f"validade do token não consultada ({e})")
print(f"login: {config.IG_LOGIN}. Para os workflows, defina IG_USER_ID={eu['user_id']} se quiser poupar uma chamada.")
