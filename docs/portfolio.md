# Como apresentar este projeto

## Resumo em 30 segundos

> Criei um laboratório que trata a saída da IA como proposta, não como autoridade. Uma
> camada determinística confere ownership, intenção, confirmação e duplicidade antes de
> qualquer efeito. As decisões ficam registradas em uma auditoria verificável.

## Demonstração rápida

1. Executar os testes unitários.
2. Rodar `scenarios/demo.jsonl`.
3. Mostrar o agendamento incompleto sendo bloqueado.
4. Mostrar o aviso de handoff liberado e a resposta automática seguinte bloqueada.
5. Verificar a cadeia de auditoria.
6. Alterar localmente um valor do log e executar a verificação novamente.
7. Rodar o health check em uma máquina Windows.

## Competências que aparecem no código

- confiabilidade: invariantes, idempotência e ownership explícito;
- operações com IA: validação independente do modelo e controle human-in-the-loop;
- observabilidade: métricas estruturadas, códigos de decisão e replay;
- segurança e privacidade: redução de dados e evidência de adulteração;
- infraestrutura: diagnóstico em PowerShell com saída JSON;
- qualidade: testes determinísticos sem rede nem chamada a modelos.

## Como explicar o escopo

> É um laboratório público feito com dados fictícios. Ele demonstra minhas decisões de
> arquitetura e a forma como testo o fluxo, mas não está conectado a clientes nem a um
> serviço de produção.
