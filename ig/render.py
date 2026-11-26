"""Renderiza slides HTML (Jinja2) em JPEG com o Chrome headless.

Feed: 1080x1350 (4:5). Vertical (stories e reels): 1080x1920 (9:16), com o conteúdo
dentro da área segura (config.FAIXA_TOPO e config.FAIXA_BASE).
"""
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from PIL import Image

from . import config, formato

_env = Environment(loader=FileSystemLoader(config.TEMPLATES), undefined=StrictUndefined, autoescape=True)
_env.filters.update(num=formato.num, sinal=formato.sinal, cartoletas=formato.cartoletas)
_env.globals.update(MANDO=formato.MANDO, POSICAO=formato.POSICAO, POSICAO_PLURAL=formato.POSICAO_PLURAL,
                    DOMINIO=config.DOMINIO, PERFIL=config.PERFIL,
                    FONTES=(config.TEMPLATES / "fontes").as_uri())


def tamanho(vertical=False):
    return (config.LARGURA, config.ALTURA_VERTICAL if vertical else config.ALTURA)


def html(template, vertical=False, reel=False, **ctx):
    vertical = vertical or reel
    w, h = tamanho(vertical)
    tela = {"largura": w, "altura": h, "vertical": vertical,
            "faixa_topo": config.FAIXA_TOPO if vertical else 0, "faixa_base": config.FAIXA_BASE if vertical else 0,
            "faixa_direita": config.FAIXA_DIREITA_REEL if reel else 0}
    ctx.setdefault("pagina", None)
    ctx.setdefault("paginas", None)
    ctx.setdefault("chamada", None)
    return _env.get_template(template).render(tela=tela, **ctx)


def slide(template, destino: Path, vertical=False, reel=False, **ctx):
    destino.parent.mkdir(parents=True, exist_ok=True)
    w, h = tamanho(vertical or reel)
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "slide.html"
        png = Path(tmp) / "slide.png"
        pagina.write_text(html(template, vertical, reel, **ctx), encoding="utf-8")
        subprocess.run([
            config.CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
            "--force-device-scale-factor=1", f"--window-size={w},{h}",
            "--virtual-time-budget=4000", "--allow-file-access-from-files",
            f"--screenshot={png}", pagina.as_uri(),
        ], check=True, capture_output=True)
        img = Image.open(png).convert("RGB")
        if img.size != (w, h):
            img = img.crop((0, 0, w, h))
        img.save(destino, "JPEG", quality=92, optimize=True, progressive=True)
    return destino
