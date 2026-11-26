# Identidade visual

A do site (cartolaemdados.com.br), aplicada nos slides de `templates/`. Fonte da verdade: as variáveis em `templates/base.html`; se mudar lá, atualize aqui.

## Tipografia
- Título: Archivo, peso 800, condensada (font-stretch 75%), caixa alta. `h1` 112px, `h2` 76px.
- Corpo: Source Serif 4. Texto de apoio (`.lead`) 36px, entrelinha 1,35.
- Dado: IBM Plex Mono, para números, rótulos, topo e rodapé (22 a 26px, caixa alta com espaçamento nos rótulos).

São três famílias, uma acima do limite da skill `direcao-de-arte`. É decisão herdada do site: a mono só aparece em número e rótulo, papel fixo, e não deve ganhar texto corrido.

## Paleta
- Fundo: papel `#F3F5F1`, papel 2 `#E8ECE5`, quadriculado `rgba(30,58,46,.07)`
- Texto: tinta `#14231C`, tinta 2 `#3D5248`, tinta 3 `#5E6F66`, linha `#C9D2CA`
- Destaque: marca-texto amarelo `#F2D43A` (fundo `rgba(242,212,58,.55)`)
- Função fixa: previsto em azul caneta `#2546A8`, gramado `#1F7A3A`, erro `#B4332A`

## Ativos distintivos
Elementos que aparecem em toda peça e fazem o perfil ser reconhecido sem logo:
- Papel quadriculado de 24px no fundo
- Marca-texto amarelo sobre o número ou palavra principal
- Caneta azul para tudo que é previsto; preto (bola cheia) para o real
- Topo com "Cartola em Dados" e "Rodada N · temporada" sobre fio preto; rodapé com o domínio e a paginação "arraste →"
- Capitão marcado com círculo amarelo de borda preta
- Só siglas dos clubes, sem escudo ou foto

## Grade padrão
- Feed 4:5, 1080 x 1350 px
- Story e reel 9:16, 1080 x 1920 px: o quadriculado cobre a tela inteira e a peça de feed fica na área segura, de 240 px do topo a 400 px da base (1280 px de altura, quase a do feed). A mesma área cabe no recorte 3:4 da grade do perfil. Medidas a verificar no aparelho; ficam em `ig/config.py`
- Story e reel não têm paginação no rodapé; a chamada para o post vai numa faixa amarela acima do rodapé (`chamada` em `base.html`)
- Margem: 72px nas laterais e no topo, 64px na base (6,7%, abaixo dos 10% da skill)
- Colunas: coluna única; tabelas e campinho definem a própria grade no template
- Calha: 36px entre itens de legenda de gráfico

## Referências
- Templates: `templates/capa_time.html`, `capa_raiox.html`, `capa_resultado.html`, `campo.html`, `banco.html`, `posicao.html`, `cartoes.html`, `halteres.html`, `cta.html`
- Peças publicadas: `fila/*/01.jpg` em diante; reels em `fila/*/video.mp4` e `capa.jpg`
