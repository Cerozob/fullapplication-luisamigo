from aws_cdk import RemovalPolicy
from aws_cdk import aws_cognito as cognito
from constructs import Construct


class Auth(Construct):
    """Registro e inicio de sesión de usuarios con Cognito."""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.user_pool = cognito.UserPool(
            self,
            "Usuarios",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            password_policy=cognito.PasswordPolicy(min_length=8),
            # Lite es el plan más barato y cubre registro, login y JWT.
            feature_plan=cognito.FeaturePlan.LITE,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Cliente público (sin secreto) para el navegador.
        self.cliente = self.user_pool.add_client(
            "Web",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_password=True),
            prevent_user_existence_errors=True,
        )
