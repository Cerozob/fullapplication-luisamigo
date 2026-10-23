# CLAUDE.md

Instrucciones para Claude Code durante la clase. Responde siempre en español.

## Qué estamos haciendo

Una clase en vivo donde se diseña y se construye desde cero una aplicación web de tareas en AWS. El objetivo es que los estudiantes **entiendan** cada pieza, no solo que funcione.

- Requisitos: `docs/01-enunciado.md`
- Decisiones ya tomadas (respétalas): `docs/03-decisiones.md`
- Supuestos de costo: `docs/04-costos.md`
- Etapas de la construcción: `docs/05-construir-con-claude-code.md`

## Reglas

- **Construye solo dentro de `construccion/`.**
- **No leas ni copies `referencia/`** salvo que el profesor lo pida explícitamente. Es la solución de respaldo y la gracia es construirla en vivo.
- **Una etapa a la vez.** Antes de escribir código, muestra un plan corto. Después de escribirlo, explica qué hace cada archivo nuevo y por qué, relacionándolo con el ADR correspondiente.
- Si algo que te piden contradice un ADR, dilo antes de hacerlo.
- Corre `cdk synth` y las pruebas antes de decir que algo está listo.
- **No ejecutes `cdk deploy` ni `cdk destroy` por tu cuenta.** Propón el comando y espera.
- Nada de secretos, llaves ni IDs de cuenta en el código.

## Stack técnico

- AWS CDK v2 en Python, región `us-east-1`. Organiza la infraestructura en un construct por capa (datos, auth, api, frontend).
- Lambda: Python 3.13, ARM64, 256 MB, logs con retención de 7 días.
- DynamoDB: `TableV2` bajo demanda, partición `usuarioId`, orden `tareaId`. Consultas con `Query`, nunca `Scan`.
- API: HTTP API (`aws_apigatewayv2`), no REST API. Límite de 10 req/s y ráfagas de 20.
- Auth: Cognito en plan Lite. El usuarioId sale del claim `sub` del JWT, nunca del cuerpo de la solicitud. Excepción a propósito: en la etapa 1 se usa temporalmente un encabezado `x-usuario`, que se elimina en la etapa 3.
- Frontend: HTML, CSS y JS sin frameworks ni build. S3 privado + CloudFront con OAC, PriceClass 100. Usa `textContent`, nunca `innerHTML`, con datos del usuario.
- Permisos: usa los `grant_*` de CDK. Nada de políticas con `*`.
- Como es una demo, los recursos usan `RemovalPolicy.DESTROY`. Menciona que en producción serían `RETAIN`.

## Estilo

- Código simple y legible para estudiantes. Comentarios breves en español que expliquen el **porqué**, no el qué.
- Nombres de dominio en español (`tareas`, `titulo`, `completada`).
