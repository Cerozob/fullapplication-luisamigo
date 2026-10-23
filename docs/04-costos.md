# 4. Estimación de costos

> Precios aproximados de us-east-1 a octubre de 2026. Antes de presentarlos a un cliente, confírmenlos en la [AWS Pricing Calculator](https://calculator.aws/). Lo importante es el método: **precio unitario × uso estimado**, capa por capa.

Supuestos: 20 solicitudes por usuario al día, Lambda de 256 MB con 100 ms por invocación, 80 % lecturas y 20 % escrituras, 1 KB por tarea.

## Precios unitarios

| Servicio | Precio | Capa gratuita |
|---|---|---|
| HTTP API | USD 1,00 por millón de solicitudes | 1 M/mes durante 12 meses (cuentas nuevas) |
| Lambda ARM | USD 0,0000133 por GB-segundo + USD 0,20 por millón | 400 000 GB-s y 1 M de solicitudes al mes, siempre |
| DynamoDB bajo demanda | USD 0,125 por millón de lecturas, USD 0,625 por millón de escrituras | 25 GB de almacenamiento, siempre |
| Cognito Lite | USD 0,0055 por usuario activo al mes | 10 000 usuarios activos al mes, siempre |
| CloudFront | USD 0,085 por GB | 1 TB y 10 M de solicitudes al mes, siempre |
| S3 | USD 0,023 por GB al mes | 5 GB durante 12 meses |
| CloudWatch Logs | USD 0,50 por GB ingerido | 5 GB al mes, siempre |

## Escenario hoy: 500 usuarios, 300 000 solicitudes al mes

| Servicio | Cálculo | Sin capa gratuita | Con capa gratuita |
|---|---|---|---|
| HTTP API | 0,3 M × 1,00 | 0,30 | 0,00 |
| Lambda | 0,3 M × 0,025 GB-s = 7 500 GB-s | 0,16 | 0,00 |
| DynamoDB | 240 000 lecturas + 60 000 escrituras | 0,07 | 0,07 |
| Cognito | 500 usuarios | 2,75 | 0,00 |
| CloudFront + S3 | unos pocos MB | 0,01 | 0,00 |
| **Total** | | **~USD 3,30** | **~USD 0,10** |

## Escenario en un año: 50 000 usuarios, 30 millones de solicitudes al mes

| Servicio | Cálculo | USD al mes |
|---|---|---|
| HTTP API | 30 M × 1,00 | 30,00 |
| Lambda | 750 000 GB-s − 400 000 gratis = 350 000 × 0,0000133, más 29 M × 0,20 | 10,50 |
| DynamoDB | 24 M lecturas × 0,125 + 6 M escrituras × 0,625 | 6,75 |
| **Cognito** | (50 000 − 10 000) × 0,0055 | **220,00** |
| CloudFront, S3 y logs | | ~3,00 |
| **Total** | | **~USD 270** |

## Lo que enseña esta tabla

1. **Sin uso cuesta casi cero.** Ese era el requisito.
2. **El costo dominante a escala no es el cómputo, es la identidad.** Nadie lo adivina sin hacer la cuenta. Opciones al llegar ahí: negociar, revisar cuántos usuarios están realmente activos o evaluar otro proveedor.
3. **La REST API habría costado USD 105** en lugar de USD 30 en el escenario grande (ADR-003).
4. **Lambda en x86** costaría ~USD 1,20 más al mes en el escenario grande. Es poco aquí, pero a gran escala el 20 % importa.
5. **Comparación:** la misma app en un EC2 t4g.small con RDS db.t4g.micro cuesta ~USD 30 al mes desde el primer día, con o sin usuarios.

## Cómo verlo en la cuenta real

- Billing → Cost Explorer, agrupado por servicio y filtrado por la etiqueta `proyecto = clase-final`. Primero hay que activarla en Billing → Cost allocation tags.
- Budgets: si se desplegó con `-c emailAlertas=...`, llega un correo al pasar el 80 % de USD 5.
