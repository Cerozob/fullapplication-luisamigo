# 5. Construir con Claude Code

> Un agente de código escribe rápido, pero **la responsabilidad sigue siendo de quien acepta el cambio**. La regla de la clase: no se despliega nada que alguien en el salón no pueda explicar.

## Cómo se trabaja con un agente

1. **Contexto primero.** `CLAUDE.md`, en la raíz, le dice al agente qué se construye, qué decisiones ya están tomadas y qué no debe hacer. Es como el documento de inducción de un compañero nuevo.
2. **Planear antes de escribir.** Activen el modo plan (`Shift+Tab` hasta ver *plan mode*) y pidan el plan. Revísenlo: ¿coincide con los ADR? Si no, corríjanlo antes de que escriba código.
3. **Pasos pequeños.** Una etapa a la vez, con una prueba o un despliegue al final de cada una.
4. **Leer el diff.** Antes de aceptar un cambio, lean qué archivos tocó y por qué. Pidan "explícame esta línea" sin pena.
5. **Verificar, no confiar.** `cdk synth`, pruebas, `curl`. Si el agente dice "listo", compruébenlo.
6. **Commit por etapa.** Así se puede volver atrás si algo se rompe.

## Antes de empezar

```bash
aws sts get-caller-identity        # ¿estoy en la cuenta correcta?
npm install -g aws-cdk             # CLI de CDK
cdk --version
claude                             # abrir Claude Code en la raíz del repo
```

La construcción en vivo va en `construccion/`. La carpeta `referencia/` es el plan B y el agente no debe leerla.

---

## Etapa 0. Esqueleto del proyecto (5 min)

**Prompt:**

```text
Lee CLAUDE.md y docs/03-decisiones.md. Crea en construccion/ un proyecto CDK en
Python vacío, con un stack llamado TareasEnVivo en us-east-1, un requirements.txt
y pytest configurado. No crees recursos todavía. Explícame qué hace cada archivo
que generes.
```

**Verificar:** `cd construccion && cdk synth` genera una plantilla vacía.

**Preguntas para la clase:** ¿qué es `cdk.json`? ¿Qué diferencia hay entre `cdk synth` y `cdk deploy`? ¿Qué hizo `cdk bootstrap` en la cuenta?

## Etapa 1. Datos y API (20 min)

**Prompt:**

```text
Etapa 1. Agrega al stack, siguiendo los ADR 002, 003, 004 y 008:
- una tabla DynamoDB bajo demanda con partición usuarioId y orden tareaId
- una sola Lambda Python 3.13 en ARM, 256 MB, con logs de 7 días, que haga el CRUD
  de /tareas y /tareas/{id}
- una HTTP API con límite de 10 req/s y ráfagas de 20
Por ahora SIN autenticación: toma el usuarioId de un encabezado x-usuario (lo
cambiaremos en la etapa 3). Organiza la infraestructura en constructs separados.
Primero muéstrame el plan.
```

**Revisar en el diff:**
- ¿Usó `grant_read_write_data` o escribió una política con `*`?
- ¿Usó `Query` por usuarioId, o `Scan`? Un `Scan` lee toda la tabla y cobra por toda la tabla.
- ¿Validó el cuerpo de la solicitud?

**Verificar:**

```bash
cdk deploy
curl -X POST -H "x-usuario: ana" -H "Content-Type: application/json" -d '{"titulo":"hola"}' <ApiUrl>tareas
curl -H "x-usuario: ana" <ApiUrl>tareas
curl -H "x-usuario: beto" <ApiUrl>tareas     # debe salir vacío
```

**Pregunta para la clase:** con un encabezado `x-usuario`, ¿qué impide que alguien lea las tareas de otro? (Nada. Por eso existe la etapa 3.)

## Etapa 2. Sitio web (15 min)

**Prompt:**

```text
Etapa 2, según el ADR-006. Crea un frontend HTML + JS sin frameworks en
construccion/frontend con una lista de tareas (crear, completar, editar, borrar).
Sírvelo desde un bucket S3 privado con CloudFront y OAC, PriceClass 100. Genera
al desplegar un config.json con la URL de la API. Configura CORS en la API solo
para el dominio de CloudFront. Usa textContent, nunca innerHTML, para los títulos.
```

**Revisar en el diff:**
- ¿El bucket tiene `BLOCK_ALL`?
- ¿Por qué CORS solo permite el dominio de CloudFront y no `*`?
- ¿Cómo llega la URL de la API al navegador sin escribirla a mano?

**Verificar:** `cdk deploy` (CloudFront tarda unos 5 minutos; buen momento para revisar los costos en [04-costos.md](04-costos.md)) y abrir `SitioUrl`.

## Etapa 3. Usuarios y seguridad (20 min)

**Prompt:**

```text
Etapa 3, según el ADR-005. Agrega un user pool de Cognito en plan Lite con
registro por correo, y un cliente web sin secreto con USER_PASSWORD_AUTH.
Protege todas las rutas de la HTTP API con un autorizador JWT de ese user pool.
En la Lambda, reemplaza el encabezado x-usuario por el claim sub del token.
En el frontend, agrega registro, confirmación por código, login y logout
llamando a la API de Cognito con fetch, sin SDK. Actualiza las pruebas.
```

**Revisar en el diff:**
- ¿La Lambda toma el usuario de `requestContext.authorizer.jwt.claims.sub`?
- ¿Queda algún rastro de `x-usuario`?
- ¿Dónde se guarda el token en el navegador y por qué `sessionStorage`?

**Verificar:** el `curl` de la etapa 1 ahora debe responder **401**. Registrarse en el sitio, confirmar el código y crear tareas.

## Etapa 4. Revisión final (opcional, 10 min)

**Prompt:**

```text
Revisa todo construccion/ contra docs/03-decisiones.md y dime, en una tabla,
qué ADR cumple cada recurso y si hay algo que no cumpla. Después estima el
costo mensual con 500 y con 50 000 usuarios usando los supuestos de
docs/04-costos.md. No cambies código.
```

**Cerrar:**

```bash
cdk destroy
```

**Pregunta final:** si el cliente pide mañana "compartir listas entre usuarios", ¿qué ADR cambia? (El ADR-002: la clave de la tabla y el patrón de acceso.)

---

## Si algo sale mal

| Síntoma | Causa probable |
|---|---|
| `cdk deploy` pide bootstrap | Falta `cdk bootstrap` en esa cuenta y región |
| El navegador muestra un error de CORS | El origen permitido no coincide con el dominio de CloudFront, o falta `authorization` en los encabezados permitidos |
| 401 con token válido | El autorizador espera otro cliente (audience). Revisen `user_pool_clients` |
| No llega el correo de Cognito | El correo por defecto permite unos 50 al día. Revisen spam |
| Se acaba el tiempo | `cd referencia && cdk deploy` |
