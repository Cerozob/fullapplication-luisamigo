from pathlib import Path

from aws_cdk import RemovalPolicy
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct

CODIGO_FRONTEND = Path(__file__).parent.parent / "frontend"


class Frontend(Construct):
    """Sitio estático: bucket S3 privado servido por CloudFront."""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            # Nadie lee el bucket directamente: solo CloudFront, vía OAC.
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.distribucion = cloudfront.Distribution(
            self,
            "Cdn",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            # Solo Norteamérica y Europa: la clase de precio más barata.
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
        )
        self.url = f"https://{self.distribucion.distribution_domain_name}"

    def publicar(self, config: dict) -> None:
        """Sube el sitio y un config.json con los datos que el navegador necesita."""
        s3deploy.BucketDeployment(
            self,
            "Despliegue",
            destination_bucket=self.bucket,
            sources=[
                s3deploy.Source.asset(str(CODIGO_FRONTEND)),
                s3deploy.Source.json_data("config.json", config),
            ],
            distribution=self.distribucion,
            distribution_paths=["/*"],
        )
