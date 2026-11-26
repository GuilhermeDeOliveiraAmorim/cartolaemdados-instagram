"""Cliente mínimo da API do Instagram.

Funciona com o login unificado (graph.facebook.com, token de sistema do portfólio) e com o
login do Instagram legado (graph.instagram.com). Os endpoints de publicação e métricas são os
mesmos; muda só como se descobre o id da conta e como se renova o token.
"""
import time
from pathlib import Path

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

    def _publicar(self, cid, video=False):
        # Vídeo processa no servidor; a Meta recomenda consultar no máximo uma vez por minuto por 5 min.
        self._esperar(cid, *((10, 30) if video else ()))
        mid = self._req("POST", f"{self.ig_id}/media_publish", creation_id=cid)["id"]
        return self._req("GET", mid, fields="id,permalink,timestamp,media_type,media_product_type")

    def _container_video(self, arquivo, url, **params):
        """Login unificado: upload resumível do arquivo local (rupload.facebook.com), sem depender de URL pública.
        A Meta restringe esse upload a alguns tipos de app; se for recusado, cai para video_url.
        Login do Instagram: o upload resumível não é documentado, vai direto por video_url."""
        if config.IG_LOGIN == "unificado":
            try:
                return self._upload_resumivel(arquivo, **params)
            except ErroIG as e:
                print(f"  upload resumível recusado ({e}); tentando por video_url")
        return self._container(video_url=url, **params)

    def _upload_resumivel(self, arquivo, **params):
        d = self._req("POST", f"{self.ig_id}/media", upload_type="resumable", **params)
        cid = d["id"]
        uri = d.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{config.IG_VERSAO}/{cid}"
        dados = Path(arquivo).read_bytes()
        r = requests.post(uri, data=dados, timeout=600, headers={
            "Authorization": f"OAuth {self.token}", "offset": "0", "file_size": str(len(dados))})
        try:
            resp = r.json()
        except ValueError:
            resp = {}
        if r.status_code >= 400 or not resp.get("success"):
            raise ErroIG(f"upload do vídeo: {r.status_code} {str(resp.get('debug_info') or resp or r.text)[:300]}")
        return cid

    def publicar(self, urls, legenda, alts=None):
        """Imagem única ou carrossel no feed."""
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
        return self._publicar(cid)

    def publicar_reel(self, arquivo, url, legenda, capa_url=None, no_feed=True):
        params = {"media_type": "REELS", "caption": legenda, "share_to_feed": "true" if no_feed else "false"}
        if capa_url:
            params["cover_url"] = capa_url
        return self._publicar(self._container_video(arquivo, url, **params), video=True)

    def publicar_story(self, imagem_url=None, arquivo=None, video_url=None):
        """Story de imagem (imagem_url) ou de vídeo (arquivo local e video_url). A API não aceita legenda em story."""
        if imagem_url:
            return self._publicar(self._container(media_type="STORIES", image_url=imagem_url))
        return self._publicar(self._container_video(arquivo, video_url, media_type="STORIES"), video=True)

    def limite(self):
        d = self._req("GET", f"{self.ig_id}/content_publishing_limit", fields="quota_usage,config")
        return (d.get("data") or [{}])[0]

    # Métricas -----------------------------------------------------------
    # Métricas válidas para cada tipo de mídia (referência de insights da mídia, revalidada em 26/11/2026).
    _FEED = ["reach", "views", "likes", "comments", "saved", "shares", "total_interactions", "follows", "profile_visits"]
    METRICAS_FORMATO = {
        "carrossel": _FEED, "imagem": _FEED,
        "reel": ["reach", "views", "likes", "comments", "saved", "shares", "total_interactions",
                 "ig_reels_avg_watch_time", "reels_skip_rate"],
        # Story: a API só devolve métricas nas primeiras 24 h, e valor abaixo de 5 vem como erro (#10).
        "story": ["reach", "views", "replies", "shares", "total_interactions", "follows", "profile_visits"],
    }
    METRICAS_POST = list(dict.fromkeys(m for ms in METRICAS_FORMATO.values() for m in ms))

    def insights_post(self, media_id, formato="carrossel"):
        """Métricas de um post. Pede uma a uma se o lote falhar (nem toda métrica vale para todo caso)."""
        metricas = self.METRICAS_FORMATO.get(formato, self._FEED)

        def ler(ms):
            d = self._req("GET", f"{media_id}/insights", metric=",".join(ms))
            return {m["name"]: (m.get("values") or [{}])[0].get("value", m.get("total_value", {}).get("value")) for m in d["data"]}
        try:
            return ler(metricas)
        except ErroIG:
            out = {}
            for m in metricas:
                try:
                    out.update(ler([m]))
                except ErroIG:
                    out[m] = None
            return out

    def campos_post(self, media_id, formato="carrossel"):
        campos = "timestamp,permalink" if formato == "story" else "like_count,comments_count,timestamp,permalink"
        return self._req("GET", media_id, fields=campos)

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
