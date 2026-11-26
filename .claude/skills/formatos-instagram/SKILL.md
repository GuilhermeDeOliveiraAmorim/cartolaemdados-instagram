---
name: formatos-instagram
description: Especificações técnicas e regras de formato do Instagram (proporções, resoluções, durações, limites, zonas de segurança). Use antes de especificar qualquer arquivo de entrega. Esta é a única skill do conjunto que envelhece rápido; sempre revalide antes de afirmar um número.
---

# Formatos e especificações

## Regra primeira
Esta skill é um retrato datado, não uma verdade. Antes de afirmar qualquer especificação em entregável, confirme na documentação oficial do Instagram ou do Meta Business. Se não puder confirmar, declare o número como "a verificar" em vez de afirmar.

Última verificação: 2026-11-26

## Retrato atual

Feed, imagem:
- Retrato 1080 x 1350 px, proporção 4:5. É o formato recomendado para feed e o que ocupa mais tela
- Quadrado 1080 x 1080 px, 1:1
- Paisagem 1080 x 566 px, 1.91:1
- Teto de arquivo na casa de 30 MB

Stories e Reels:
- 1080 x 1920 px, 9:16
- Mantenha texto, logo e CTA fora das faixas de interface no topo e na base

Reels, vídeo (confirmado na referência da API de publicação, `media_type=REELS`, em 2026-11-26):
- MP4 ou MOV, sem edit list, moov no início do arquivo
- H.264 ou HEVC, progressivo, GOP fechado, 4:2:0; 23 a 60 fps; largura máxima 1920 px; até 25 Mbps
- Áudio AAC, até 48 kHz, mono ou estéreo, 128 kbps
- Duração de 3 s a 15 min; arquivo até 300 MB; 9:16 recomendado
- Capa (`cover_url`): JPEG, até 8 MB, sRGB
- Pela API não dá para escolher música da biblioteca do Instagram; o reel sai com o áudio do arquivo
- Larguras abaixo de 720 px degradam visivelmente

Stories pela API (`media_type=STORIES`, confirmado em 2026-11-26):
- Imagem JPEG até 8 MB, sRGB, 9:16 recomendado
- Vídeo com as mesmas exigências do reel, de 3 s a 60 s e até 100 MB
- Sem legenda, sem sticker (link, enquete, local) e sem colaborador; menção sem sticker é aceita
- Métricas só nas primeiras 24 h

Faixas de interface no 9:16: a medida exata não está na documentação oficial. Neste projeto o conteúdo fica entre 240 px do topo e 400 px da base (a verificar no aparelho).

Carrossel:
- Uma proporção para o post inteiro. A primeira mídia define o enquadramento das demais
- Até 10 cartões no uso publicitário; o limite do post orgânico é maior e muda com frequência, confirme
- Construa todos os slides na mesma tela e mantenha elementos recorrentes na mesma posição

## Como manter esta skill viva
1. Mensalmente, buscar a página oficial de especificações e atualizar a data acima
2. Registrar mudanças em CHANGELOG.md nesta pasta, com data e o que mudou
3. Anotar aqui os formatos novos da plataforma assim que aparecerem, mesmo sem número confirmado

## Limites que mudam e precisam de checagem a cada uso
- Número de caracteres de legenda
- Número e comportamento de hashtags
- Duração máxima de Reels (3 s a 15 min pela API em 2026-11-26)
- Quantidade de slides em carrossel orgânico
- Formatos de colaboração, enquetes e links em stories
