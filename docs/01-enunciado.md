# 1. El enunciado

> Así llega casi siempre un proyecto: un cliente con una necesidad, poco presupuesto y prisa. El primer trabajo del arquitecto es convertir esto en requisitos.

## Lo que dice el cliente

"Somos una startup pequeña. Queremos una aplicación web de **tareas** para que cada persona lleve su lista desde el computador o el celular. Cada usuario se registra con su correo y solo ve sus propias tareas. Puede crearlas, editarlas, marcarlas como hechas y borrarlas.

Arrancamos con unos **500 usuarios**. Si funciona, en un año podríamos tener **50 000**. Somos **un solo desarrollador**, no tenemos a nadie de operaciones y el presupuesto es casi cero mientras validamos la idea. Queremos salir en **una semana**."

## Ejercicio: ¿qué le preguntarían al cliente?

Antes de dibujar nada, la clase propone preguntas. Algunas que deberían salir:

- ¿Desde dónde se conectan los usuarios? (Latinoamérica, ¿algún otro país?)
- ¿Se necesita trabajar sin conexión?
- ¿Hay datos sensibles? (salud, pagos, datos personales más allá del correo)
- ¿Se comparten tareas entre usuarios o en equipos?
- ¿Se necesitan reportes o búsquedas complejas?
- ¿Qué pasa si la aplicación se cae una hora? ¿Y si se pierden datos?
- ¿Login con Google u otras redes?

## Respuestas del cliente (para seguir el ejercicio)

| Pregunta | Respuesta |
|---|---|
| Ubicación | Latinoamérica, sobre todo Costa Rica y Colombia |
| Sin conexión | No por ahora |
| Datos sensibles | Solo el correo y el texto de las tareas |
| Compartir | No en la primera versión |
| Reportes | No. Solo la lista de cada usuario |
| Caída | Una hora es tolerable. Perder datos no |
| Login social | Más adelante, quizá |

## Requisitos resultantes

**Funcionales**

1. Registro con correo y confirmación por código.
2. Inicio y cierre de sesión.
3. Crear, listar, editar, completar y borrar tareas.
4. Cada usuario solo accede a sus tareas.

**No funcionales**

| Atributo | Requisito | Por qué importa en el diseño |
|---|---|---|
| Costo | Cercano a USD 0 sin uso, y crece con el uso | Descarta servidores encendidos 24/7 |
| Operación | Sin servidores que parchar | Un solo desarrollador |
| Escala | De 500 a 50 000 usuarios sin rediseñar | Necesitamos escalado automático |
| Seguridad | HTTPS, aislamiento por usuario, mínimo privilegio | Datos personales |
| Durabilidad | No perder datos | Base de datos administrada |
| Disponibilidad | Una hora de caída es tolerable | No hace falta multirregión |
| Tiempo | Una semana | Servicios administrados y poco código |

Siguiente paso: [2. Diseño guiado](02-diseno-guiado.md).
