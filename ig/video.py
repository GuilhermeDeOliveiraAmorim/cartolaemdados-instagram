"""Monta o MP4 de um reel ou story em vídeo a partir de cenas estáticas (JPEG 1080x1920).

Cada cena fica na tela pelo tempo pedido; a troca é corte seco ou fusão curta.
Saída no formato que a API aceita: H.264 high, yuv420p, 30 fps, GOP fechado, AAC 48 kHz
estéreo (faixa silenciosa), MP4 com moov no início e sem edit list.
"""
import subprocess
from pathlib import Path

from PIL import Image

from . import config

FUSAO = 0.3  # segundos


def compor(cenas, destino: Path, fps=config.FPS):
    """cenas: [(caminho_jpg, segundos, fundir)], fundir=True faz fusão com a cena anterior."""
    w, h = config.LARGURA, config.ALTURA_VERTICAL
    cmd = [
        config.FFMPEG, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-map", "0:v", "-map", "1:a", "-shortest",
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-preset", "medium",
        "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-g", str(fps * 2), "-sc_threshold", "0",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", "-use_editlist", "0", str(destino),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    anterior = None
    quadros = 0
    try:
        for caminho, segundos, fundir in cenas:
            img = Image.open(caminho).convert("RGB")
            if img.size != (w, h):
                raise ValueError(f"{caminho}: {img.size}, esperado {(w, h)}")
            n = max(1, round(segundos * fps))
            k = min(n, round(FUSAO * fps)) if fundir and anterior is not None else 0
            for i in range(k):
                proc.stdin.write(Image.blend(anterior, img, (i + 1) / (k + 1)).tobytes())
            bruto = img.tobytes()
            for _ in range(n - k):
                proc.stdin.write(bruto)
            quadros += n
            anterior = img
        proc.stdin.close()
    except BrokenPipeError:
        pass
    erro = proc.stderr.read().decode()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg falhou: {erro[-1000:]}")
    return quadros / fps
