# Laboratório de Confiabilidade para Operações de IA

Este é um laboratório público e totalmente sintético sobre fluxos de IA confiáveis:
barreiras determinísticas, ownership humano, handoff protegido por integridade,
auditoria verificável, logs com redução de dados pessoais e testes de regressão.

[Read in English](README.md)

## O problema

Uma IA pode produzir uma resposta convincente e, ainda assim, propor uma ação errada.
Fila saudável, API respondendo e ausência de exceções não provam que a decisão está
correta. Este projeto coloca uma **barreira de commit** entre a proposta da IA e o efeito
simulado.

O modelo pode interpretar e propor. A autoridade final permanece em regras explícitas,
estado verificável e ownership humano.

## O que o código comprova

- A automação é bloqueada quando um humano assume a conversa.
- Um único aviso de handoff pode atravessar a trava, desde que seu conteúdo corresponda
  ao hash previamente autorizado.
- Uma intenção de remarcação não pode criar silenciosamente um novo agendamento.
- Ações sensíveis exigem serviço, data e horário confirmados.
- Eventos repetidos são bloqueados por idempotência.
- O log de auditoria usa uma cadeia SHA-256 capaz de detectar adulteração.
- E-mails e telefones são reduzidos antes de serem persistidos no log.
- Métricas de decisões e handoffs ficam disponíveis em um snapshot de saúde.

Todos os dados e diálogos são fictícios. O código foi escrito como implementação pública
original e não possui vínculo com empregadores, clientes ou sistemas de produção.

## Executar

Requer Python 3.11 ou mais recente e não utiliza dependências externas em runtime.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
ai-ops-lab demo --scenario scenarios/demo.jsonl --audit artifacts/demo-audit.jsonl
ai-ops-lab verify --audit artifacts/demo-audit.jsonl
```

Para coletar um health check de uma máquina Windows:

```powershell
.\scripts\windows-health-check.ps1 -OutputPath .\artifacts\windows-health.json
```

Consulte a [arquitetura](docs/architecture.md), o [runbook](docs/runbook.md) e o
[mapa de competências e evidências](skills.json).
