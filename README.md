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
GitHub Actions token.yml     toda segunda: renova o token do Instagram
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

1. **Conta profissional.** No app do Instagram: Configurações, Tipo de conta e ferramentas, Mudar para conta profissional (Criador de conteúdo ou Empresa). Não precisa de Página do Facebook.
2. **App na Meta.** Em [developers.facebook.com](https://developers.facebook.com/apps), crie um app do tipo Empresa com o caso de uso de Instagram ("API do Instagram com login do Instagram"). Os nomes no painel mudam com frequência; o caminho é o caso de uso do Instagram, configuração da API com login do Instagram.
3. **Permissões.** `instagram_business_basic`, `instagram_business_content_publish` e `instagram_business_manage_insights`. Para uso na própria conta, com o app em modo de desenvolvimento e a conta adicionada como testadora, não precisa de revisão do app.
4. **Token.** Na mesma tela, adicione a conta @cartolaemdados e gere o token. Ele é de longa duração (60 dias) e o `token.yml` renova toda semana. Confira localmente:
   ```bash
   IG_TOKEN='...' .venv/bin/python checar.py
   ```
5. **Repositório público no GitHub** com este diretório, branch `main`.
6. **Secrets do repositório** (Settings, Secrets and variables, Actions):
   - `IG_TOKEN`: o token do passo 4.
   - `GH_PAT`: token fine-grained do GitHub só deste repositório, com permissão *Secrets: Read and write* (usado pelo `token.yml` para regravar o `IG_TOKEN`).
7. **Actions.** Settings, Actions, General, Workflow permissions: *Read and write*. Rode o `Métricas` uma vez à mão (`workflow_dispatch`) para validar o token no Actions.

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
renovar_token.py   renova o token (Actions)
checar.py          confere token, conta e cota de publicação
ig/                config, leitura dos dados, renderização, fila, cliente da API
ig/pautas/         uma pauta por arquivo: monta slides, legenda e horário
templates/         HTML/CSS dos slides (1080×1350) e as fontes do site (OFL)
fila/              posts gerados, aprovados e publicados
metricas/          CSVs e relatório
```

Pauta nova: um arquivo em `ig/pautas/` com `montar(temporada, rodada, opcoes)` e o registro em `ig/pautas/__init__.py`.
