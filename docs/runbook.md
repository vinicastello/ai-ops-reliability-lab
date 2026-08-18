# Runbook operacional

## Objetivo

Este documento explica como executar o cenário fictício, verificar a cadeia de
auditoria e investigar uma proposta bloqueada. Nenhuma etapa opera um sistema externo.

## Antes de começar

1. Use Python 3.11 ou superior.
2. Confirme que `artifacts/` não contém um arquivo que precise ser preservado.
3. Execute os testes antes de analisar a saída da demonstração.

```bash
python -m unittest discover -s tests -v
```

## Executar o cenário

```bash
ai-ops-lab demo \
  --scenario scenarios/demo.jsonl \
  --audit artifacts/demo-audit.jsonl
```

O último objeto JSON apresenta saúde, integridade do ledger, ownership ativo e
contadores.

## Verificar a auditoria

```bash
ai-ops-lab verify --audit artifacts/demo-audit.jsonl
```

Resultado esperado:

```json
{"valid": true, "message": "verified 10 record(s)"}
```

A quantidade exata pode mudar conforme o cenário evoluir.

## Investigar um bloqueio

1. Localize o `event_id` na saída da CLI.
2. Encontre a entrada `proposal_decided` no arquivo de auditoria.
3. Confira `decision.code` e `decision.reasons`.
4. Garanta que `state_after` não registrou a transição proibida.
5. Reproduza o caso em um teste antes de alterar a política.

## Códigos de decisão

| Código | Significado |
|---|---|
| `POLICY_PASS` | Todas as regras ativas foram atendidas |
| `DUPLICATE_EVENT` | O evento já havia sido efetivado |
| `HUMAN_OWNERSHIP_LOCK` | A automação tentou agir durante atendimento humano |
| `AUTHORIZED_HANDOFF_NOTICE` | O aviso exato e de uso único foi liberado |
| `INTENT_ACTION_MISMATCH` | A ação proposta conflita com a intenção |
| `MISSING_CONFIRMED_FIELDS` | Faltam evidências para uma ação sensível |
| `EMPTY_RESPONSE` | Foi proposto um efeito sem resposta explícita |

## Regra para incidentes

Não enfraqueça uma invariante global para fazer um caso isolado passar. Primeiro
identifique se o erro está na proposta, no estado ou na política; depois escreva um
teste que reproduza a falha e o comportamento esperado.
