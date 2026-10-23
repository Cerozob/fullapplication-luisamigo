from aws_cdk import RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class Datos(Construct):
    """Tabla de tareas. Una sola tabla: usuarioId (partición) + tareaId (orden)."""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.tabla = dynamodb.TableV2(
            self,
            "Tabla",
            partition_key=dynamodb.Attribute(name="usuarioId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="tareaId", type=dynamodb.AttributeType.STRING),
            # Bajo demanda: se paga por solicitud, $0 cuando nadie la usa.
            billing=dynamodb.Billing.on_demand(),
            # Es una demo de clase. En producción sería RETAIN.
            removal_policy=RemovalPolicy.DESTROY,
        )
