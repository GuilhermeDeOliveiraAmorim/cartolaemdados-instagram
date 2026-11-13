"""Confere o token: conta, seguidores e quanto da cota de publicação (24 h) já foi usado.

  IG_TOKEN=... python checar.py
"""
import os

from ig.api import Instagram

ig = Instagram(os.environ["IG_TOKEN"])
eu = ig.eu()
print(f"@{eu['username']} (id {eu['user_id']}): {eu.get('followers_count')} seguidores, {eu.get('media_count')} posts")
lim = ig.limite()
print(f"cota de publicação: {lim.get('quota_usage')} usados de {(lim.get('config') or {}).get('quota_total')} em 24 h")
