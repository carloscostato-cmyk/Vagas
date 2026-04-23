---
name: three-teams-operating-model
description: Opera o projeto com 3 times paralelos e papéis fixos (gerente de projetos, analista de sistemas, analista de processos, analista de testes) sob coordenação central. Use quando o usuário pedir diagnóstico completo, feedback por papel, operação simultânea dos times, status do sistema no GitHub, plano de correção ou acompanhamento da execução.
---

# Three Teams Operating Model

## Estrutura fixa

Sempre considerar esta estrutura durante análises e execuções:

- Time 1: Aquisição de Vagas
- Time 2: Notificação e Comunicação
- Time 3: Dashboard e Observabilidade

Cada time possui:

1. Gerente de Projetos
2. Analista de Sistemas
3. Analista de Processos
4. Analista de Testes

O agente principal coordena os 3 times, consolida conflitos e define prioridade final.

## Modo de execução

1. Ler rapidamente arquivos centrais do fluxo.
2. Produzir diagnóstico técnico objetivo do estado atual.
3. Identificar falhas que impedem execução em produção.
4. Propor correções em ordem de prioridade.
5. Quando solicitado, aplicar as correções e validar.

## Formato obrigatório de feedback

Quando o usuário pedir "feedback completo", responder neste formato:

- Time 1 (Aquisição): 4 feedbacks (GP, Sistemas, Processos, Testes)
- Time 2 (Notificação): 4 feedbacks (GP, Sistemas, Processos, Testes)
- Time 3 (Dashboard): 4 feedbacks (GP, Sistemas, Processos, Testes)
- Coordenação central: riscos cruzados + plano final

Cada feedback deve conter:

- Status: OK, Atenção ou Crítico
- Evidência: arquivo/símbolo analisado
- Impacto: efeito no funcionamento
- Ação: correção recomendada

## Regras práticas

- Priorizar bugs reais e bloqueios de execução.
- Não inventar logs externos; basear-se no código e artefatos disponíveis.
- Se faltar evidência externa (ex.: logs do Actions), indicar exatamente o que coletar.
- Sempre informar a URL do dashboard ao final:
  - https://carloscostato-cmyk.github.io/Vagas/
