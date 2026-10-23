import importlib.util
import json
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

RUTA_HANDLER = Path(__file__).parent.parent / "lambda" / "tareas" / "handler.py"


@pytest.fixture
def handler(monkeypatch):
    monkeypatch.setenv("TABLA", "tareas")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "prueba")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "prueba")
    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName="tareas",
            KeySchema=[
                {"AttributeName": "usuarioId", "KeyType": "HASH"},
                {"AttributeName": "tareaId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "usuarioId", "AttributeType": "S"},
                {"AttributeName": "tareaId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        spec = importlib.util.spec_from_file_location("handler", RUTA_HANDLER)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        yield modulo


def evento(ruta, usuario="ana", id=None, cuerpo=None):
    return {
        "routeKey": ruta,
        "pathParameters": {"id": id} if id else None,
        "body": json.dumps(cuerpo) if cuerpo is not None else None,
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": usuario}}}},
    }


def llamar(handler, *args, **kwargs):
    r = handler.handler(evento(*args, **kwargs), None)
    return r["statusCode"], json.loads(r["body"]) if r.get("body") else None


def test_crud_completo(handler):
    codigo, tarea = llamar(handler, "POST /tareas", cuerpo={"titulo": " Estudiar CDK "})
    assert codigo == 201
    assert tarea["titulo"] == "Estudiar CDK"
    assert tarea["completada"] is False
    assert "usuarioId" not in tarea

    codigo, tareas = llamar(handler, "GET /tareas")
    assert codigo == 200
    assert [t["tareaId"] for t in tareas] == [tarea["tareaId"]]

    codigo, actualizada = llamar(handler, "PUT /tareas/{id}", id=tarea["tareaId"], cuerpo={"completada": True})
    assert codigo == 200
    assert actualizada["completada"] is True
    assert actualizada["titulo"] == "Estudiar CDK"

    codigo, _ = llamar(handler, "DELETE /tareas/{id}", id=tarea["tareaId"])
    assert codigo == 204
    assert llamar(handler, "GET /tareas/{id}", id=tarea["tareaId"])[0] == 404


def test_un_usuario_no_ve_tareas_de_otro(handler):
    _, tarea = llamar(handler, "POST /tareas", usuario="ana", cuerpo={"titulo": "Privada"})

    assert llamar(handler, "GET /tareas", usuario="beto")[1] == []
    assert llamar(handler, "GET /tareas/{id}", usuario="beto", id=tarea["tareaId"])[0] == 404
    assert llamar(handler, "PUT /tareas/{id}", usuario="beto", id=tarea["tareaId"], cuerpo={"titulo": "x"})[0] == 404
    assert llamar(handler, "DELETE /tareas/{id}", usuario="beto", id=tarea["tareaId"])[0] == 404


@pytest.mark.parametrize(
    "cuerpo",
    [{}, {"titulo": ""}, {"titulo": "   "}, {"titulo": 5}, {"titulo": "x" * 201}],
)
def test_titulo_invalido(handler, cuerpo):
    assert llamar(handler, "POST /tareas", cuerpo=cuerpo)[0] == 400


def test_actualizar_sin_cambios_o_tipo_incorrecto(handler):
    _, tarea = llamar(handler, "POST /tareas", cuerpo={"titulo": "Algo"})
    assert llamar(handler, "PUT /tareas/{id}", id=tarea["tareaId"], cuerpo={})[0] == 400
    assert llamar(handler, "PUT /tareas/{id}", id=tarea["tareaId"], cuerpo={"completada": "si"})[0] == 400


def test_cuerpo_no_json(handler):
    r = handler.handler({**evento("POST /tareas"), "body": "no es json"}, None)
    assert r["statusCode"] == 400
