"""Renderiza slides HTML (Jinja2) em JPEG 1080x1350 com o Chrome headless."""
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


def html(template, **ctx):
    return _env.get_template(template).render(**ctx)


def slide(template, destino: Path, **ctx):
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "slide.html"
        png = Path(tmp) / "slide.png"
        pagina.write_text(html(template, **ctx), encoding="utf-8")
        subprocess.run([
            config.CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
            "--force-device-scale-factor=1", f"--window-size={config.LARGURA},{config.ALTURA}",
            "--virtual-time-budget=4000", "--allow-file-access-from-files",
            f"--screenshot={png}", pagina.as_uri(),
        ], check=True, capture_output=True)
        img = Image.open(png).convert("RGB")
        if img.size != (config.LARGURA, config.ALTURA):
            img = img.crop((0, 0, config.LARGURA, config.ALTURA))
        img.save(destino, "JPEG", quality=92, optimize=True, progressive=True)
    return destino
