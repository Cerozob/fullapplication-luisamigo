# Solución de referencia

Aplicación completa y probada. Sirve como plan B en clase: si la construcción en vivo se atasca, se despliega esta.

## Qué crea

| Capa | Servicio | Archivo |
|---|---|---|
| Sitio web | S3 privado + CloudFront (OAC) | `infra/frontend.py`, `frontend/` |
| Identidad | Cognito (plan Lite) | `infra/auth.py` |
| API | API Gateway HTTP API + autorizador JWT | `infra/api.py` |
| Lógica | Una Lambda Python en ARM | `lambda/tareas/handler.py` |
| Datos | DynamoDB bajo demanda | `infra/datos.py` |
| Costos | Límite de solicitudes, logs de 7 días, presupuesto opcional | `infra/api.py`, `infra/stack.py` |

CDK también crea dos Lambdas auxiliares: una sube el sitio al bucket y otra lo vacía al destruir el stack.

## Desplegar

```bash
cd referencia
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest                                     # 15 pruebas
cdk bootstrap                                        # una sola vez por cuenta y región
cdk deploy                                           # o: cdk deploy -c emailAlertas=su@correo.com
```

El despliegue tarda de 5 a 8 minutos, casi todo por CloudFront. Al terminar, abra la salida `SitioUrl`.

## Probar la API con curl

```bash
TOKEN=$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH \
  --client-id <ClienteId> --auth-parameters USERNAME=<correo>,PASSWORD=<clave> \
  --query AuthenticationResult.AccessToken --output text)

curl -H "Authorization: Bearer $TOKEN" <ApiUrl>tareas
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"titulo":"Probar la API"}' <ApiUrl>tareas
```

## Limpiar

```bash
cdk destroy
```

Todo usa `RemovalPolicy.DESTROY` porque es una demo. En producción, la tabla y el user pool serían `RETAIN`.
