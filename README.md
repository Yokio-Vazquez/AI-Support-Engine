# AI Support Engine

## Estado de la implementación

La parte 1 contiene:

- Motor tradicional basado en reglas.
- Esquemas compartidos con Pydantic.
- Endpoint `POST /api/analyze`.
- Validación de entrada.
- Respuestas predeterminadas.
- Pruebas de motor y API.

La parte generativa se integrará en `app/routes/analyze.py` y requerirá una implementación
real del motor en `app/services/generative_engine.py`.

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

Documentación interactiva:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

## Ejemplo tradicional

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/analyze" `
  -H "Content-Type: application/json" `
  -d '{\"message\":\"No puedo iniciar sesion\",\"mode\":\"traditional\"}'
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
