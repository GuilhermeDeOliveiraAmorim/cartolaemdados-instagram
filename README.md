# Instagram do Cartola em Dados

Automação do [@cartolaemdados](https://www.instagram.com/cartolaemdados/): gera os posts a partir do modelo do `cartola-dados`, agenda, publica pela API oficial do Instagram e coleta as métricas.

## Conceito

O perfil é a vitrine do diário do modelo (`cartolaemdados.com.br`): o time sai **antes** da bola rolar e o resultado **depois**, acerte ou erre. A identidade visual é a do site: papel quadriculado, marca-texto amarelo, caneta azul para o previsto.

| Momento | Pauta | Formato | Quando publica | O que mostra |
| --- | --- | --- | --- | --- |
| Antes do fechamento | `raio-x` | carrossel, 8 slides | assim que aprovar; expira 10 min antes do fechamento | top 5 de projeção por posição, com teto e quem está no time |
| Antes do fechamento | `time-modelo` | carrossel, 4 slides | assim que aprovar; expira 10 min antes do fechamento | capa com a projeção, campinho, banco, Luxo e consenso que ficou de fora |
| Depois da rodada | `previsto-real` | carrossel, 4 slides | próximo 12:00 | pontos contra projeção, jogador a jogador, destaques |
| Depois da rodada | `temporada` | carrossel, 3 slides | dia seguinte, 18:00 | acumulado previsto × real das rodadas registradas ao vivo |

Regras do conteúdo (as mesmas do site):

- Times de especialistas só aparecem agregados (mediana e contagem), nunca com nome de time ou autor.
- Ausência de dado aparece como `–`, nunca como `0`.
- Sem travessão em nenhum texto (a legenda com travessão derruba a geração).
- Sem escudos ou fotos da Globo: só siglas dos clubes.

## Fluxo

```
cartola-dados (/escalar, /pos-rodada)
        │  exportar_diario.py (contrato v1 do site)
        ▼
gerar.py pre|pos --pr      local: renderiza os JPEG e abre um PR com a prévia
        │
        ▼  merge do PR = aprovação
GitHub Actions publicar.yml  no merge e a cada 30 min: publica o que está no horário
GitHub Actions metricas.yml  todo dia 09:00: métricas dos posts e da conta, metricas/RELATORIO.md
GitHub Actions token.yml     toda segunda: renova o token (só no login do Instagram legado)
```

As imagens são servidas pelo próprio repositório (`raw.githubusercontent.com`, fixado no commit), por isso **o repositório precisa ser público**. Os segredos ficam nos Secrets do GitHub, nunca no código.

## Uso

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt

# depois do /escalar no cartola-dados
.venv/bin/python gerar.py pre --pr

# depois do /pos-rodada (a média do Cartola é opcional)
.venv/bin/python gerar.py pos --media-cartola 52.3 --pr

# uma pauta, rodada e horário específicos, sem PR (para revisar as imagens em fila/)
.venv/bin/python gerar.py previsto-real --rodada 33 --quando "2026-11-14 12:00"
```

- `gerar.py` lê `../cartola-dados` e `../cartola` (troque com `CARTOLA_DADOS` e `CARTOLA_SITE`) e precisa do Google Chrome (`CHROME`).
- Cada post vira `fila/<temporada>-<rodada>-<pauta>/` com `post.json`, `legenda.txt` e `01.jpg`, `02.jpg`...
- Regerar um post não publicado sobrescreve a pasta. Post publicado não é regerado.
- `publicar.py --simular` mostra o que seria publicado agora.
- `metricas.py --so-relatorio` regrava o relatório sem chamar a API.

Para tirar um post da fila antes de publicar: apague a pasta em `main` ou mude `agendado_para` no `post.json`.

## Configuração (uma vez)

Desde o fim de outubro de 2026, a Meta recomenda o **login unificado** para a API do Instagram, Este projeto aceita os dois tipos de token e decide pelo prefixo: `EA...` é token de sistema do login unificado (API em `graph.facebook.com`, não expira); `IG...` é token do login do Instagram (API em `graph.instagram.com`, vale 60 dias e o `token.yml` renova). Para forçar, defina a variável `IG_LOGIN` (`unificado` ou `instagram`).

1. **Conta profissional** no Instagram (Criador de conteúdo ou Empresa). Não precisa de Página do Facebook.
2. **App na Meta** ([developers.facebook.com/apps](https://developers.facebook.com/apps)): Criar app, caso de uso **Gerenciar mensagens e conteúdo no Instagram**, sem portfólio no assistente.
3. **Portfólio empresarial.** Em Casos de uso, Personalizar, **API setup with Unified login**: conecte um portfólio próprio do Cartola em Dados (criar é grátis; para uso na própria conta não precisa de verificação).
4. **Configuração** na mesma aba: permissões obrigatórias mais `instagram_content_publish` e `instagram_manage_insights`; expiração do token **Nunca**, se houver a opção; URL de redirecionamento `https://cartolaemdados.com.br/` (obrigatória, não é usada).
5. **Token.** Em Gerar tokens de acesso, adicione o @cartolaemdados como testador do Instagram, aceite o convite (Instagram na web: Configurações, Permissões do site, Apps e sites, Convites de testador) e clique em Gerar token. Ele aparece uma vez só. Com o app em modo de desenvolvimento, não precisa de análise do app.
6. **Confira e grave o segredo**, sem o token passar pelo histórico do shell:
   ```bash
   read -rs -p "Token: " IG_TOKEN && echo && export IG_TOKEN \
     && .venv/bin/python checar.py \
     && printf %s "$IG_TOKEN" | gh secret set IG_TOKEN -R GuilhermeDeOliveiraAmorim/cartolaemdados-instagram
   ```
   O `checar.py` mostra a conta, a cota de publicação e quando o token vence.
7. **Validade.** O token de sistema não é renovado pelo `token.yml` (ele só age com `IG_LOGIN=instagram`). Se o `checar.py` mostrar uma data de expiração, gere um novo no painel antes dela.

## Métricas

- `metricas/posts.csv`: uma linha por post e por dia, nos 30 dias depois da publicação (alcance, views, curtidas, comentários, salvos, compartilhamentos, interações, seguidores ganhos, visitas ao perfil). Dá a curva de cada post.
- `metricas/conta.csv`: uma linha por dia (seguidores, alcance, visitas ao perfil, cliques no link, quem seguiu e deixou de seguir). Algumas métricas de conta só aparecem com 100 seguidores ou mais; até lá ficam vazias.
- `metricas/RELATORIO.md`: tabela por post, médias por pauta (alcance, salvos e compartilhamentos sobre o alcance) e alerta para a pauta que fica abaixo de 60% do alcance médio em 3 posts ou mais.

A API não dá métrica de cada slide de um carrossel, só do post inteiro.

## Estrutura

```
gerar.py           gera os posts na fila (local) e abre o PR
publicar.py        publica o que está no horário (Actions)
metricas.py        coleta métricas e gera o relatório (Actions)
renovar_token.py   renova o token do login do Instagram legado (Actions)
checar.py          confere token, conta e cota de publicação
ig/                config, leitura dos dados, renderização, fila, cliente da API
ig/pautas/         uma pauta por arquivo: monta slides, legenda e horário
templates/         HTML/CSS dos slides (1080×1350) e as fontes do site (OFL)
fila/              posts gerados, aprovados e publicados
metricas/          CSVs e relatório
```

Pauta nova: um arquivo em `ig/pautas/` com `montar(temporada, rodada, opcoes)` e o registro em `ig/pautas/__init__.py`.
