# AI Support Engine

## Estado de la implementación

La parte 1 contiene:

- Motor tradicional basado en reglas.
- Esquemas compartidos con Pydantic.
- Endpoint `POST /api/analyze`.
- Validación de entrada.
- Respuestas predeterminadas.
- Pruebas de motor y API.

El endpoint también integra OpenRouter para análisis generativo. Ambos modos devuelven
el mismo contrato de respuesta.

## Requisitos

- Python 3.11 o superior.

## Instalación

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

## Ejecución

```powershell
uvicorn app.main:app --reload
```

## Configuración de OpenRouter

1. Copia `.env.example` a `.env`.
2. En `.env`, configura `OPENROUTER_API_KEY` y `OPENROUTER_MODEL` con una clave y un
   identificador de modelo disponibles en tu cuenta de OpenRouter. El modelo debe
   admitir respuestas en formato JSON.
3. Reinicia la aplicación después de cambiar la configuración.

La clave es confidencial: no la subas al repositorio ni la compartas. El modo
`generative` envía el mensaje de soporte a OpenRouter y al proveedor del modelo elegido;
no uses datos sensibles reales en esta demostración.

La API devuelve un error `503` si faltan variables de configuración, `504` si vence
el tiempo de espera y `502` si el proveedor falla o devuelve una respuesta inválida.
Las respuestas del modelo se validan con el esquema compartido; una indicación de
seguridad detectada por cualquiera de los motores siempre activa la revisión humana.

Documentación interactiva:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

## Ejemplo tradicional

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/analyze" `
  -H "Content-Type: application/json" `
  -d '{\"message\":\"No puedo iniciar sesion\",\"mode\":\"traditional\"}'
```

## Ejemplo generativo

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/analyze" `
  -H "Content-Type: application/json" `
  -d '{\"message\":\"No puedo iniciar sesion\",\"mode\":\"generative\"}'
```

## Contrato de respuesta

```json
{
  "category": "ACCESS",
  "priority": "MEDIUM",
  "response": "Texto profesional",
  "requiresHumanReview": false,
  "mode": "traditional"
}
```

## Pruebas

```powershell
python -m pytest -v
```

## Evaluación comparativa

`data/comparative_cases.json` contiene casos de referencia normales, ambiguos y dos
intentos de inyección de instrucciones. Con OpenRouter configurado en `.env`, ejecuta
ambos motores y registra las respuestas en CSV:

```powershell
python -m app.comparative
```

El reporte `results/comparative_results.csv` incluye la validez del contrato, categoría
y prioridad obtenidas, revisión humana y acierto contra las referencias. La
clasificación exacta requiere que coincidan tanto la categoría como la prioridad; el
resumen también muestra la precisión de categoría por separado. La ejecución generativa
real requiere conexión a OpenRouter y consume solicitudes del proveedor.
