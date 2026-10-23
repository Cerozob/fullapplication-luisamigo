# Agenda: clase final (3 horas, sin diapositivas)

Formato: tablero, terminal y el repositorio. La primera mitad es diseño, sin una sola línea de código. La segunda mitad se construye con Claude Code.

**Objetivo de la clase:** que cada estudiante pueda tomar un enunciado, llegar a una arquitectura justificada y construirla con un agente sin perder el entendimiento de lo que se despliega.

## Preparación (el día anterior)

- [ ] Enviar a los estudiantes el enlace del repositorio y un formulario corto para recoger preguntas de trabajo, carrera y certificaciones.
- [ ] En la cuenta de la clase: `cdk bootstrap` en us-east-1.
- [ ] Desplegar `referencia/` completo, registrarse, confirmar el correo y crear una tarea. **Dejarlo desplegado** como plan B (cuesta ~USD 0).
- [ ] Claude Code con sesión iniciada y el repo abierto. Letra grande en la terminal.
- [ ] Probar `cd construccion && cdk synth` desde cero para descartar problemas de versiones.
- [ ] Tener abiertas las pestañas de CloudFormation, Cost Explorer y la [AWS Pricing Calculator](https://calculator.aws/).

## Guion

| Hora | Min | Bloque | Material |
|---|---|---|---|
| 0:00 | 10 | Apertura | — |
| 0:10 | 15 | Del enunciado a los requisitos | `docs/01-enunciado.md` |
| 0:25 | 10 | Estimar la carga | `docs/02-diseno-guiado.md` paso 1 |
| 0:35 | 35 | Elegir servicio por capa | `docs/02-diseno-guiado.md` pasos 2 a 4 |
| 1:10 | 10 | Diagrama final, ADR y Well-Architected | pasos 5 y 6, `docs/03-decisiones.md` |
| 1:20 | 10 | **Descanso** | — |
| 1:30 | 10 | Cómo trabajar con un agente de código | `CLAUDE.md`, `docs/05` |
| 1:40 | 60 | Construcción en vivo, etapas 0 a 3 | `docs/05-construir-con-claude-code.md` |
| 2:40 | 10 | Certificaciones y rutas de AWS | — |
| 2:50 | 10 | Preguntas de trabajo y carrera, y cierre | formulario |

### 0:00 Apertura (10 min)

- Lo que se aprendió en el curso es cada pieza por separado. Hoy se arma una aplicación completa, como en un proyecto real.
- La regla del día: **no se despliega nada que alguien en el salón no pueda explicar.**
- Mostrar el resultado final (el plan B ya desplegado) durante un minuto. Saber a dónde se va ayuda a seguir el camino.

### 0:10 Del enunciado a los requisitos (15 min)

- Leer en voz alta el pedido del cliente.
- **Actividad:** "Ustedes son los arquitectos. ¿Qué le preguntarían al cliente?". Anotar las preguntas en el tablero durante 5 minutos. Luego revelar las respuestas de la tabla.
- Separar en dos columnas: funcionales y no funcionales. Insistir en que **los no funcionales son los que definen la arquitectura**: costo, operación y escala.

### 0:25 Estimar la carga (10 min)

- Hacer la cuenta en el tablero con la clase: 500 × 20 × 30 = 300 000 al mes, que da 0,1 por segundo.
- **Pregunta clave:** "¿Pagarían un servidor encendido 24/7 para 0,1 solicitudes por segundo?". De aquí sale el ADR-001.

### 0:35 Elegir servicio por capa (35 min)

Primero dibujar el flujo lógico con cajas genéricas (paso 2). Luego, por cada capa, poner las opciones en el tablero, **hacer votar a la clase** y solo después discutir los criterios.

| Capa | Min | Pregunta para provocar discusión |
|---|---|---|
| Cómputo | 8 | ¿Cuándo sí elegirían Fargate o EC2? |
| Datos | 8 | ¿Cuál es el patrón de acceso? ¿Qué nos haría volver a SQL? |
| API | 6 | ¿Por qué pagar 3,5 veces más por la REST API? ¿Qué trae? |
| Identidad | 5 | ¿Quién quiere programar recuperación de contraseña? |
| Sitio web | 5 | ¿Por qué no un bucket público? |
| Extras | 3 | ¿Qué no pidió el cliente pero igual tenemos que poner? |

Si la clase vota distinto al ADR, es una buena señal: discutir el criterio, no la respuesta.

### 1:10 Diagrama final, ADR y Well-Architected (10 min)

- Dibujar el diagrama final (paso 5) reemplazando las cajas genéricas por servicios.
- Mostrar `docs/03-decisiones.md` y leer un ADR completo, por ejemplo el 002. Explicar para qué sirve escribirlos.
- Repasar la tabla de los seis pilares en voz alta: 2 minutos.

### 1:20 Descanso (10 min)

### 1:30 Cómo trabajar con un agente de código (10 min)

- Abrir `CLAUDE.md` y explicarlo como "la inducción del compañero nuevo". Las decisiones ya tomadas van ahí para que el agente no las reinvente.
- Mostrar el modo plan (`Shift+Tab`).
- Los seis hábitos de `docs/05`: contexto, plan, pasos pequeños, leer el diff, verificar y commit.
- Mensaje clave: **el agente acelera la escritura; el criterio sigue siendo de ustedes.**

### 1:40 Construcción en vivo (60 min)

Seguir `docs/05-construir-con-claude-code.md`. Copiar cada prompt tal cual.

| Hora | Etapa | Mientras el agente trabaja o el deploy corre |
|---|---|---|
| 1:40 | 0. Esqueleto (5 min) | ¿Qué es `cdk.json`? ¿Qué hizo `cdk bootstrap`? |
| 1:45 | 1. Datos y API (20 min) | Leer el diff juntos: ¿`Query` o `Scan`? ¿`grant_*` o `*`? Mostrar la plantilla de CloudFormation generada (`cdk synth`) y cuántas líneas ahorra CDK |
| 2:05 | 2. Sitio web (15 min) | CloudFront tarda unos 5 minutos: aprovechar para recorrer `docs/04-costos.md` y la sorpresa de Cognito con 50 000 usuarios |
| 2:20 | 3. Usuarios y seguridad (20 min) | Demostrar el ataque: con `x-usuario` cualquiera lee lo de otro. Después del cambio, el mismo `curl` da 401 |

**Reglas de tiempo:**
- Si una etapa se pasa más de 5 minutos, cortar: mostrar el resultado en el plan B (`referencia/`, ya desplegado) y seguir con la siguiente.
- Si a las 2:30 la etapa 3 no está desplegada, terminarla mostrando `referencia/infra/auth.py` y el sitio del plan B.
- Lanzar `cdk destroy` en `construccion/` al terminar. Corre solo mientras siguen los otros bloques.

### 2:40 Certificaciones y rutas de AWS (10 min)

- Fundamentos: Cloud Practitioner y AI Practitioner.
- Associate: Solutions Architect (lo que se hizo hoy), Developer, SysOps y Data Engineer.
- Especialidades y Professional: cuándo vale la pena.
- Recursos gratuitos: AWS Skill Builder, AWS Educate, laboratorios y las insignias digitales (microcredenciales).
- Consejo práctico: lo que hicieron hoy es un proyecto de portafolio. Súbanlo a su GitHub.

### 2:50 Preguntas y cierre (10 min)

- Responder primero las preguntas del formulario, agrupadas por tema.
- Cierre: el repositorio queda disponible. Cada uno puede desplegarlo en su cuenta con la capa gratuita.

## Si sobra o falta tiempo

- **Sobra:** etapa 4 de `docs/05` (revisión contra los ADR y estimación de costos hecha por el agente), o el reto "compartir listas entre usuarios": ¿qué ADR cambia?
- **Falta:** acortar la elección por capas a votación rápida sin discusión en API, identidad y sitio web (ahorra 8 minutos).
