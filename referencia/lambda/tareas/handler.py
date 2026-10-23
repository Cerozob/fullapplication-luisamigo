"""CRUD de tareas. Una sola Lambda atiende todas las rutas de la HTTP API.

Cada usuario solo ve sus tareas: el usuarioId sale del token JWT que ya
validó API Gateway, nunca del cuerpo de la solicitud.
"""

import base64
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

_tabla = None


def tabla():
    # Se crea una vez por contenedor y se reutiliza entre invocaciones.
    global _tabla
    if _tabla is None:
        _tabla = boto3.resource("dynamodb").Table(os.environ["TABLA"])
    return _tabla


def handler(event, context):
    usuario = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    ruta = event["routeKey"]
    tarea_id = (event.get("pathParameters") or {}).get("id")

    try:
        if ruta == "GET /tareas":
            return listar(usuario)
        if ruta == "POST /tareas":
            return crear(usuario, leer_cuerpo(event))
        if ruta == "GET /tareas/{id}":
            return obtener(usuario, tarea_id)
        if ruta == "PUT /tareas/{id}":
            return actualizar(usuario, tarea_id, leer_cuerpo(event))
        if ruta == "DELETE /tareas/{id}":
            return eliminar(usuario, tarea_id)
    except ValueError as error:
        return respuesta(400, {"error": str(error)})

    return respuesta(404, {"error": "Ruta no encontrada"})


def listar(usuario):
    resultado = tabla().query(KeyConditionExpression=Key("usuarioId").eq(usuario))
    tareas = sorted((publica(t) for t in resultado["Items"]), key=lambda t: t["creadaEn"])
    return respuesta(200, tareas)


def crear(usuario, cuerpo):
    tarea = {
        "usuarioId": usuario,
        "tareaId": str(uuid.uuid4()),
        "titulo": validar_titulo(cuerpo.get("titulo")),
        "completada": False,
        "creadaEn": datetime.now(timezone.utc).isoformat(),
    }
    tabla().put_item(Item=tarea)
    return respuesta(201, publica(tarea))


def obtener(usuario, tarea_id):
    resultado = tabla().get_item(Key={"usuarioId": usuario, "tareaId": tarea_id})
    if "Item" not in resultado:
        return respuesta(404, {"error": "Tarea no encontrada"})
    return respuesta(200, publica(resultado["Item"]))


def actualizar(usuario, tarea_id, cuerpo):
    cambios = {}
    if "titulo" in cuerpo:
        cambios["titulo"] = validar_titulo(cuerpo["titulo"])
    if "completada" in cuerpo:
        if not isinstance(cuerpo["completada"], bool):
            raise ValueError("completada debe ser true o false")
        cambios["completada"] = cuerpo["completada"]
    if not cambios:
        raise ValueError("Envíe titulo o completada")

    try:
        resultado = tabla().update_item(
            Key={"usuarioId": usuario, "tareaId": tarea_id},
            UpdateExpression="SET " + ", ".join(f"#{c} = :{c}" for c in cambios),
            ExpressionAttributeNames={f"#{c}": c for c in cambios},
            ExpressionAttributeValues={f":{c}": v for c, v in cambios.items()},
            # Sin esta condición, update_item crearía una tarea nueva.
            ConditionExpression="attribute_exists(tareaId)",
            ReturnValues="ALL_NEW",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return respuesta(404, {"error": "Tarea no encontrada"})
        raise
    return respuesta(200, publica(resultado["Attributes"]))


def eliminar(usuario, tarea_id):
    try:
        tabla().delete_item(
            Key={"usuarioId": usuario, "tareaId": tarea_id},
            ConditionExpression="attribute_exists(tareaId)",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return respuesta(404, {"error": "Tarea no encontrada"})
        raise
    return {"statusCode": 204}


def leer_cuerpo(event):
    cuerpo = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        cuerpo = base64.b64decode(cuerpo).decode("utf-8")
    try:
        datos = json.loads(cuerpo)
    except json.JSONDecodeError:
        raise ValueError("El cuerpo debe ser JSON válido")
    if not isinstance(datos, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON")
    return datos


def validar_titulo(titulo):
    if not isinstance(titulo, str) or not titulo.strip():
        raise ValueError("El título es obligatorio")
    if len(titulo) > 200:
        raise ValueError("El título admite máximo 200 caracteres")
    return titulo.strip()


def publica(tarea):
    # El usuarioId es interno: no se devuelve al navegador.
    return {k: v for k, v in tarea.items() if k != "usuarioId"}


def respuesta(codigo, cuerpo):
    return {
        "statusCode": codigo,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(cuerpo, ensure_ascii=False),
    }
