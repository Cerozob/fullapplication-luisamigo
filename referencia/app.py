#!/usr/bin/env python3
import aws_cdk as cdk

from infra.stack import TareasStack

app = cdk.App()

# La configuración se lee solo aquí y se pasa al stack como parámetros.
email_alertas = app.node.try_get_context("emailAlertas")

TareasStack(
    app,
    "Tareas",
    email_alertas=email_alertas,
    env=cdk.Environment(region="us-east-1"),
)

cdk.Tags.of(app).add("proyecto", "clase-final")
app.synth()
