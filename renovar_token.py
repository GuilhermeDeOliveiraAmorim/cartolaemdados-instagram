"""Renova o token de longa duração do Instagram (vale 60 dias) e imprime o novo.

O workflow token.yml roda isso toda semana e grava o resultado no segredo IG_TOKEN.
"""
import os

from ig.api import Instagram

novo, expira = Instagram(os.environ["IG_TOKEN"]).renovar_token()
print(f"::add-mask::{novo}")
with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
    f.write(f"token={novo}\n")
print(f"token renovado, expira em {int(expira or 0) // 86400} dias")
