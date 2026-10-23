# 3. Registro de decisiones de arquitectura (ADR)

> Un ADR deja escrito **qué** se decidió, **por qué** y **qué se descartó**. Dentro de un año, alguien (o uno mismo) va a preguntar "¿por qué DynamoDB y no PostgreSQL?". La respuesta tiene que estar aquí, no en la memoria de nadie.

Plantilla:

```markdown
## ADR-000: Título
- Estado: propuesta | aceptada | reemplazada por ADR-xxx
- Contexto: qué problema o requisito obliga a decidir
- Decisión: qué elegimos
- Alternativas: qué descartamos y por qué
- Consecuencias: qué ganamos y qué aceptamos perder
```

---

## ADR-001: Arquitectura serverless

- **Estado:** aceptada
- **Contexto:** un solo desarrollador, sin equipo de operaciones, costo cercano a cero sin uso y tráfico de 0,1 a 120 solicitudes por segundo.
- **Decisión:** usar servicios administrados que cobran por uso: Lambda, DynamoDB, HTTP API, Cognito, S3 y CloudFront.
- **Alternativas:** EC2 o Fargate con RDS. Tienen un costo fijo de USD 25 o más al mes y requieren operación.
- **Consecuencias:** costo proporcional al uso y nada que parchar. Aceptamos arranques en frío y cierta dependencia de AWS.

## ADR-002: DynamoDB con usuarioId como partición

- **Estado:** aceptada
- **Contexto:** el único patrón de acceso es "las tareas de un usuario". No hay reportes ni joins.
- **Decisión:** una tabla bajo demanda con partición `usuarioId` y orden `tareaId`.
- **Alternativas:** RDS PostgreSQL, descartado por su costo fijo y por la gestión de conexiones desde Lambda.
- **Consecuencias:** listar las tareas es una sola consulta y el aislamiento por usuario queda en la clave. Si mañana se necesitan reportes, se exportan a S3 y se consultan con Athena.

## ADR-003: HTTP API en lugar de REST API

- **Estado:** aceptada
- **Contexto:** necesitamos rutas CRUD, CORS y validación de JWT de Cognito.
- **Decisión:** API Gateway HTTP API con autorizador JWT.
- **Alternativas:** la REST API cuesta 3,5 veces más y sus funciones extra (planes de uso, caché, transformaciones) no se necesitan. Una Function URL no tiene autorizador JWT ni límite de solicitudes.
- **Consecuencias:** es más barata y simple. Si se necesitara WAF directamente en la API, habría que reconsiderar.

## ADR-004: Una sola Lambda para todas las rutas

- **Estado:** aceptada
- **Contexto:** son cinco operaciones CRUD pequeñas sobre la misma tabla.
- **Decisión:** una Lambda que enruta por `routeKey`.
- **Alternativas:** una Lambda por ruta, con permisos más finos por operación, pero cinco veces más recursos y más arranques en frío.
- **Consecuencias:** menos piezas y menos arranques en frío. Si una operación creciera mucho o necesitara otros permisos, se separa.

## ADR-005: Cognito Lite con autorizador JWT

- **Estado:** aceptada
- **Contexto:** registro con correo y aislamiento por usuario, sin programar autenticación.
- **Decisión:** user pool de Cognito en plan Lite. La HTTP API valida el token y la Lambda toma el `sub` del token como usuarioId.
- **Alternativas:** autenticación propia (riesgosa y lenta) o un proveedor externo (otra factura y otro proveedor).
- **Consecuencias:** 10 000 usuarios activos al mes gratis, y la Lambda nunca confía en un usuarioId enviado por el navegador. Con 50 000 usuarios, Cognito pasa a ser el mayor costo (ver [costos](04-costos.md)).
- **Nota de clase:** el frontend usa el flujo `USER_PASSWORD_AUTH` por simplicidad. En producción se prefiere la página de login administrada de Cognito con código y PKCE, o el flujo SRP.

## ADR-006: S3 privado + CloudFront con OAC

- **Estado:** aceptada
- **Contexto:** sitio estático con HTTPS, rápido en Latinoamérica y barato.
- **Decisión:** bucket privado servido solo por CloudFront con Origin Access Control, en la clase de precio 100.
- **Alternativas:** un bucket público (sin HTTPS propio y abierto a internet) o Amplify Hosting (válido, con menos control).
- **Consecuencias:** el bucket nunca es público. La clase de precio 100 sirve Latinoamérica desde los puntos de Norteamérica, con algo más de latencia que la clase de precio completa y menor costo.

## ADR-007: Infraestructura como código con CDK en Python

- **Estado:** aceptada
- **Contexto:** hay que poder recrear y destruir todo, revisar cambios en Git y no hacer clics en la consola.
- **Decisión:** AWS CDK en Python.
- **Alternativas:** CloudFormation puro (verboso, unas 600 líneas de YAML para este stack) o Terraform (excelente y multinube, pero otro lenguaje, HCL, y un estado que hay que administrar).
- **Consecuencias:** un lenguaje que la clase ya conoce, construcciones de alto nivel (`grant_read_write_data`) y el estado lo maneja CloudFormation.

## ADR-008: Protecciones de costo desde el día uno

- **Estado:** aceptada
- **Contexto:** una cuenta de estudiante o de startup no puede recibir una factura sorpresa.
- **Decisión:** límite de 10 solicitudes por segundo con ráfagas de 20 en la API, logs con retención de 7 días, Lambda en ARM y presupuesto de USD 5 con alerta al 80 %.
- **Alternativas:** no poner nada y revisar la factura a fin de mes.
- **Consecuencias:** el límite rechaza tráfico por encima de 10 solicitudes por segundo. Hoy sobra, pero hay que subirlo al crecer.
