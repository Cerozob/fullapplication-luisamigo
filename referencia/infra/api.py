from pathlib import Path

from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk.aws_apigatewayv2_authorizers import HttpUserPoolAuthorizer
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct

CODIGO_LAMBDA = Path(__file__).parent.parent / "lambda" / "tareas"


class Api(Construct):
    """HTTP API protegida con Cognito, con una sola Lambda que atiende el CRUD."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        tabla: dynamodb.ITableV2,
        user_pool: cognito.IUserPool,
        cliente: cognito.IUserPoolClient,
        origen_permitido: str,
    ) -> None:
        super().__init__(scope, construct_id)

        # Retención corta: los logs también cuestan.
        log_group = logs.LogGroup(
            self,
            "Logs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.funcion = lambda_.Function(
            self,
            "Funcion",
            runtime=lambda_.Runtime.PYTHON_3_13,
            # ARM (Graviton) cuesta ~20 % menos que x86 por GB-segundo.
            architecture=lambda_.Architecture.ARM_64,
            memory_size=256,
            timeout=Duration.seconds(10),
            handler="handler.handler",
            code=lambda_.Code.from_asset(str(CODIGO_LAMBDA)),
            environment={"TABLA": tabla.table_name},
            log_group=log_group,
        )
        # Mínimo privilegio: solo esta tabla, solo lectura y escritura de datos.
        tabla.grant_read_write_data(self.funcion)

        autorizador = HttpUserPoolAuthorizer("Cognito", user_pool, user_pool_clients=[cliente])

        self.http_api = apigwv2.HttpApi(
            self,
            "Api",
            default_authorizer=autorizador,
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=[origen_permitido],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.PUT,
                    apigwv2.CorsHttpMethod.DELETE,
                ],
                allow_headers=["authorization", "content-type"],
                max_age=Duration.days(1),
            ),
            create_default_stage=False,
        )

        # Límite de solicitudes: protege la factura si alguien abusa de la API.
        etapa = apigwv2.HttpStage(
            self,
            "Etapa",
            http_api=self.http_api,
            stage_name="$default",
            auto_deploy=True,
            throttle=apigwv2.ThrottleSettings(rate_limit=10, burst_limit=20),
        )
        self.url = etapa.url

        integracion = HttpLambdaIntegration("Lambda", self.funcion)
        self.http_api.add_routes(
            path="/tareas",
            methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.POST],
            integration=integracion,
        )
        self.http_api.add_routes(
            path="/tareas/{id}",
            methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.PUT, apigwv2.HttpMethod.DELETE],
            integration=integracion,
        )
