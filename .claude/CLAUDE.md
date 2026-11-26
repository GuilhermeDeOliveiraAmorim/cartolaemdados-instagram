# Agentes de conteúdo do @cartolaemdados

Subagentes em `.claude/agents/` e skills em `.claude/skills/`. Não entram no fluxo da rodada (`gerar.py` continua automático, acionado pelo `cartola-dados`); servem para pauta nova, mudança de legenda ou arte de uma pauta existente e análise de métricas. Nessas demandas, siga a ordem sem pular etapas:

1. `estrategista-conteudo` decide se a peça deve existir e com que ângulo
2. `copywriter` escreve o texto (que vira código em `ig/pautas/`)
3. `diretor-de-arte` (carrossel, em `templates/`) ou `roteirista-reels` (vídeo, ainda sem pipeline) especifica a execução
4. `revisor-senior` aprova ou devolve com pendências
5. `analista-performance` fecha o ciclo com `metricas/` e alimenta o próximo

## Regras

* O contexto do perfil vive em `contexto/` (perfil, tom de voz, identidade visual). Agente lê o arquivo, não pergunta o que já está escrito. Campo marcado "a preencher" vira suposição declarada.
* Histórico de testes em `metricas/testes.md`, atualização obrigatória a cada teste.
* Nenhum agente afirma comportamento de algoritmo como fato nem inventa número de desempenho, depoimento ou especificação técnica.
* Especificação de plataforma vem da skill `formatos-instagram`, sempre revalidada; o que não foi confirmado é marcado "a verificar".
* As regras do conteúdo do projeto (mercado fechado, especialistas só agregados, `–` para ausência, sem travessão, só siglas) valem acima de qualquer skill.
