from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_budgets as budgets
from constructs import Construct

from infra.api import Api
from infra.auth import Auth
from infra.datos import Datos
from infra.frontend import Frontend


class TareasStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        email_alertas: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        datos = Datos(self, "Datos")
        auth = Auth(self, "Auth")
        frontend = Frontend(self, "Frontend")
        api = Api(
            self,
            "Api",
            tabla=datos.tabla,
            user_pool=auth.user_pool,
            cliente=auth.cliente,
            origen_permitido=frontend.url,
        )

        frontend.publicar(
            {
                "region": self.region,
                "apiUrl": api.url,
                "clienteId": auth.cliente.user_pool_client_id,
            }
        )

        if email_alertas:
            self._presupuesto(email_alertas)

        CfnOutput(self, "SitioUrl", value=frontend.url)
        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "UserPoolId", value=auth.user_pool.user_pool_id)
        CfnOutput(self, "ClienteId", value=auth.cliente.user_pool_client_id)

    def _presupuesto(self, email: str) -> None:
        """Alerta por correo cuando el gasto de la cuenta pasa el 80 % de USD 5 al mes."""
        budgets.CfnBudget(
            self,
            "Presupuesto",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=5, unit="USD"),
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        notification_type="ACTUAL",
                        comparison_operator="GREATER_THAN",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(subscription_type="EMAIL", address=email)
                    ],
                )
            ],
        )
