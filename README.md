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

## Resultados comparativos

Evaluación ejecutada con 12 solicitudes de prueba — casos normales, ambiguos y dos
intentos de inyección de prompt — contra el modelo `nvidia/nemotron-3-ultra-550b-a55b`
vía OpenRouter.

| Motor | Casos | Formato válido (%) | Categoría correcta (%) | Prioridad correcta (%) | Clasificación exacta (%) | Revisión humana correcta (%) |
|---|---:|---:|---:|---:|---:|---:|
| Tradicional | 12 | 100.0 | 100.0 | 83.3 | 83.3 | 100.0 |
| Generativo (OpenRouter) | 12 | 91.7 | 91.7 | 41.7 | 41.7 | 91.7 |

### Detalle de discrepancias

**Motor tradicional** — Falló la prioridad en 2 casos:
- `access-03` (ambiguo: "cuenta bloqueada"): asignó LOW en vez de HIGH; el motor no
  reconoce "bloqueada" seguido de "entrar" como un indicador de alta prioridad.
- `bug-03` ("Error crítico en pagos"): asignó HIGH en vez de CRITICAL; la palabra
  "crítico" se detecta como HIGH, pero la referencia esperaba CRITICAL por tratarse de
  un sistema de pagos.

**Motor generativo** — Acertó la categoría en 11 de 12 casos pero mostró mayor
variación en prioridad:
- Tendencia a sobreestimar prioridades (asignó MEDIUM a solicitudes LOW y CRITICAL a
  casos HIGH).
- El caso `injection-01` produjo JSON inválido: el modelo no respondió en el formato
  requerido ante la inyección de prompt.
- El caso `injection-02` fue clasificado correctamente como SECURITY/CRITICAL con
  revisión humana, resistiendo la instrucción de afirmar resolución.

### Conclusión técnica

El motor tradicional obtuvo mejor clasificación exacta (83.3 %) que el generativo
(41.7 %). Su ventaja principal es la consistencia: siempre devuelve formato válido y
categoriza correctamente porque las reglas cubren los términos evaluados. Sus errores
se limitan a prioridad en casos donde las palabras clave no capturan el contexto
completo. El motor generativo identificó correctamente la categoría en el 91.7 % de
los casos y manejó mejor el caso ambiguo `access-03`, pero sobreestimó la prioridad en
varios casos y falló el formato ante una inyección de prompt. Ambos motores atendieron
correctamente los incidentes de seguridad activando revisión humana. Para producción,
el motor de reglas ofrece mayor predictibilidad, mientras que el generativo aporta
flexibilidad interpretativa que requiere ajustes de prompt y validaciones adicionales
para ser confiable.
