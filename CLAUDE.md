# Instagram do Cartola em Dados

Automação do @cartolaemdados: gera os posts a partir do modelo do `cartola-dados` (clone em `../cartola-dados`), publica pela API oficial do Instagram no GitHub Actions e coleta as métricas. Detalhes de uso e configuração no `README.md`.

## Quem aciona

O fluxo da rodada é conduzido pelo `cartola-hub` (clone em `../cartola-hub`), na skill `publicar-instagram` (`../cartola-hub/.claude/skills/publicar-instagram/SKILL.md`), depois da `publicar-site`. As regras de publicação comuns ao site e ao Instagram, com o glossário, estão em `../cartola-hub/docs/regras-publicacao.md`. Ela roda `gerar.py pre|pos --pr` daqui. O merge do PR em `main` é a aprovação e publica no horário de cada pauta, por isso exige confirmação explícita do usuário.

## O que este repo lê do `cartola-dados`

O contrato está em `../cartola-dados/docs/instagram.md`. Em resumo:

* `exportar_diario.py` (JSON do diário, contrato v1 do site), rodado em `../cartola-dados`.
* `dados_api/<T>/rodada-N/modelo/<UTC>/projecoes.csv` (execução mais recente) para o raio-x.
* `dados_api/<T>/rodada-N/pre/status.json` (`fechamento`) para o horário dos posts pré.
* `content/rodadas/<T>-<NN>.json` no `origin/master` do site (`../cartola`) para notas e média do Cartola.

Mudou algo disso lá, confira aqui. Mudou a leitura aqui, atualize o `docs/instagram.md` de lá.

## Regras do conteúdo

* O time do modelo (escalação, capitão, banco, raio-x) só sai depois do fechamento: posts pré publicam a partir dele, como o site. Pautas sem o time podem publicar com o mercado aberto.
* Times de especialistas só agregados, sem nome de time ou autor.
* Ausência de dado é `–`, nunca `0`.
* Só siglas dos clubes, sem escudos ou fotos da Globo.

## Git

* `main` é produção: o Actions publica o que está na fila de `main`.
* Posts entram por PR (`gerar.py --pr`). Código entra por branch e PR para `main`, Conventional Commits com prefixo em inglês e mensagem em PT-BR, com o rodapé de atribuição padrão.
* O Actions commita direto em `main` (`chore(fila): estado da publicação`, `chore(metricas): coleta de ...`). Antes de criar branch, `git pull --ff-only`.

## Idioma e estilo

PT-BR em tudo. Nunca usar travessão (`—`), nem em legenda (derruba a geração). Mensagens curtas e diretas, sem narrar os passos.
