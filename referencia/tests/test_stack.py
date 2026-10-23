"""Pruebas de la infraestructura: verifican las decisiones de costo y seguridad."""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from infra.stack import TareasStack


@pytest.fixture(scope="module")
def plantilla():
    app = cdk.App()
    stack = TareasStack(app, "Prueba", env=cdk.Environment(region="us-east-1"))
    return Template.from_stack(stack)


def test_tabla_bajo_demanda(plantilla):
    plantilla.has_resource_properties("AWS::DynamoDB::GlobalTable", {"BillingMode": "PAY_PER_REQUEST"})


def test_lambda_arm_con_logs_de_una_semana(plantilla):
    plantilla.has_resource_properties(
        "AWS::Lambda::Function",
        {"Architectures": ["arm64"], "Runtime": "python3.13", "MemorySize": 256},
    )
    plantilla.has_resource_properties("AWS::Logs::LogGroup", {"RetentionInDays": 7})


def test_http_api_con_limite_y_rutas_protegidas(plantilla):
    plantilla.has_resource_properties("AWS::ApiGatewayV2::Api", {"ProtocolType": "HTTP"})
    plantilla.has_resource_properties(
        "AWS::ApiGatewayV2::Stage",
        {"StageName": "$default", "DefaultRouteSettings": {"ThrottlingRateLimit": 10, "ThrottlingBurstLimit": 20}},
    )
    rutas = plantilla.find_resources("AWS::ApiGatewayV2::Route")
    assert len(rutas) == 5
    assert all(r["Properties"]["AuthorizationType"] == "JWT" for r in rutas.values())


def test_cognito_plan_lite(plantilla):
    plantilla.has_resource_properties("AWS::Cognito::UserPool", {"UserPoolTier": "LITE"})


def test_bucket_privado_y_cloudfront_barato(plantilla):
    plantilla.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )
    plantilla.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {"DistributionConfig": Match.object_like({"PriceClass": "PriceClass_100", "DefaultRootObject": "index.html"})},
    )
    plantilla.resource_count_is("AWS::CloudFront::OriginAccessControl", 1)


def test_presupuesto_solo_con_email():
    app = cdk.App()
    stack = TareasStack(app, "ConAlertas", email_alertas="profe@ejemplo.com", env=cdk.Environment(region="us-east-1"))
    Template.from_stack(stack).resource_count_is("AWS::Budgets::Budget", 1)
