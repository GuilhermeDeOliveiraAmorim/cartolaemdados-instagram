"""Cliente mínimo da API do Instagram.

Funciona com o login unificado (graph.facebook.com, token de sistema do portfólio) e com o
login do Instagram legado (graph.instagram.com). Os endpoints de publicação e métricas são os
mesmos; muda só como se descobre o id da conta e como se renova o token.
"""
import time

import requests

from . import config


class ErroIG(Exception):
    pass


class Instagram:
    def __init__(self, token):
        self.token = token
        self.base = f"{config.IG_HOST}/{config.IG_VERSAO}"
        self._id = config.IG_USER_ID

    def _req(self, metodo, caminho, **params):
        params["access_token"] = self.token
        url = caminho if caminho.startswith("http") else f"{self.base}/{caminho}"
        r = requests.request(metodo, url, params=params if metodo == "GET" else None,
                             data=params if metodo == "POST" else None, timeout=60)
        dados = r.json() if r.content else {}
        if r.status_code >= 400 or "error" in dados:
            erro = dados.get("error", {})
            raise ErroIG(f"{metodo} {caminho}: {r.status_code} {erro.get('message', r.text)[:300]}")
        return dados

    @property
    def ig_id(self):
        if not self._id:
            if config.IG_LOGIN == "unificado":
                contas = self._req("GET", "me/assigned_instagram_accounts", fields="id,username")["data"]
                if not contas:
                    raise ErroIG("o token não tem nenhuma conta do Instagram atribuída")
                if len(contas) > 1:
                    raise ErroIG("mais de uma conta atribuída: defina IG_USER_ID (" +
                                 ", ".join(f"{c.get('username')}={c['id']}" for c in contas) + ")")
                self._id = contas[0]["id"]
            else:
                self._id = self._req("GET", "me", fields="user_id")["user_id"]
        return self._id

    def eu(self):
        d = self._req("GET", self.ig_id, fields="username,followers_count,follows_count,media_count")
        d["user_id"] = self.ig_id
        return d

    # Publicação ---------------------------------------------------------
    def _container(self, **params):
        return self._req("POST", f"{self.ig_id}/media", **params)["id"]

    def _esperar(self, cid, tentativas=10, pausa=6):
        for _ in range(tentativas):
            status = self._req("GET", cid, fields="status_code")["status_code"]
            if status == "FINISHED":
                return
            if status in ("ERROR", "EXPIRED"):
                raise ErroIG(f"container {cid}: {status}")
            time.sleep(pausa)
        raise ErroIG(f"container {cid} não ficou pronto")

    def publicar(self, urls, legenda, alts=None):
        alts = alts or [None] * len(urls)
        if len(urls) == 1:
            cid = self._container(image_url=urls[0], caption=legenda, **({"alt_text": alts[0][:1000]} if alts[0] else {}))
        else:
            filhos = []
            for u, alt in zip(urls, alts):
                filhos.append(self._container(image_url=u, is_carousel_item="true", **({"alt_text": alt[:1000]} if alt else {})))
            for f in filhos:
                self._esperar(f)
            cid = self._container(media_type="CAROUSEL", children=",".join(filhos), caption=legenda)
        self._esperar(cid)
        mid = self._req("POST", f"{self.ig_id}/media_publish", creation_id=cid)["id"]
        info = self._req("GET", mid, fields="id,permalink,timestamp,media_type")
        return info

    def limite(self):
        d = self._req("GET", f"{self.ig_id}/content_publishing_limit", fields="quota_usage,config")
        return (d.get("data") or [{}])[0]

    # Métricas -----------------------------------------------------------
    METRICAS_POST = ["reach", "views", "likes", "comments", "saved", "shares", "total_interactions", "follows", "profile_visits"]

    def insights_post(self, media_id):
        """Métricas de um post. Pede uma a uma se o lote falhar (nem toda métrica vale para todo tipo)."""
        def ler(metricas):
            d = self._req("GET", f"{media_id}/insights", metric=",".join(metricas))
            return {m["name"]: (m.get("values") or [{}])[0].get("value", m.get("total_value", {}).get("value")) for m in d["data"]}
        try:
            return ler(self.METRICAS_POST)
        except ErroIG:
            out = {}
            for m in self.METRICAS_POST:
                try:
                    out.update(ler([m]))
                except ErroIG:
                    out[m] = None
            return out

    def campos_post(self, media_id):
        return self._req("GET", media_id, fields="like_count,comments_count,timestamp,permalink")

    METRICAS_CONTA = ["reach", "views", "profile_views", "accounts_engaged", "total_interactions", "website_clicks", "follows_and_unfollows"]

    def insights_conta(self, desde, ate):
        """Totais da conta entre dois timestamps unix (janela de um dia)."""
        out = {}
        for m in self.METRICAS_CONTA:
            try:
                extra = {"breakdown": "follow_type"} if m == "follows_and_unfollows" else {}
                d = self._req("GET", f"{self.ig_id}/insights", metric=m, period="day", metric_type="total_value",
                              since=int(desde), until=int(ate), **extra)
                tv = d["data"][0].get("total_value", {})
                if m == "follows_and_unfollows":
                    for b in (tv.get("breakdowns") or [{}])[0].get("results", []):
                        out["seguiu" if b["dimension_values"] == ["FOLLOWER"] else "deixou"] = b["value"]
                else:
                    out[m] = tv.get("value")
            except (ErroIG, IndexError, KeyError):
                out.setdefault(m, None)
        return out

    # Token --------------------------------------------------------------
    def renovar_token(self):
        """Só no login do Instagram legado. O token de sistema do login unificado não usa isso."""
        if config.IG_LOGIN == "unificado":
            raise ErroIG("renovação automática só existe no login do Instagram (IG_LOGIN=instagram)")
        d = self._req("GET", "https://graph.instagram.com/refresh_access_token", grant_type="ig_refresh_token")
        return d["access_token"], d.get("expires_in")
