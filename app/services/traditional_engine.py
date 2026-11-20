import re

from app.schemas import AnalysisResult


ACCESS_TERMS = (
    "iniciar sesion",
    "iniciar sesión",
    "login",
    "contraseña",
    "password",
    "credencial",
    "cuenta bloqueada",
    "recuperar acceso",
    "acceso",
)

BUG_TERMS = (
    "error",
    "fallo",
    "falla",
    "bug",
    "excepcion",
    "excepción",
    "crash",
    "no carga",
    "no funciona",
    "incorrecto",
)

FEATURE_TERMS = (
    "nueva funcion",
    "nueva función",
    "funcionalidad",
    "agregar",
    "añadir",
    "quiero",
    "me gustaría",
    "solicitud",
)

SECURITY_TERMS = (
    "vulnerabilidad",
    "cve",
    "ransomware",
    "malware",
    "phishing",
    "filtracion",
    "filtración",
    "ataque",
    "intrusion",
    "intrusión",
    "acceso no autorizado",
    "secreto expuesto",
    "datos robados",
)

CRITICAL_TERMS = (
    "brecha",
    "datos robados",
    "acceso no autorizado",
    "ransomware",
    "activo",
    "en curso",
)

HIGH_TERMS = (
    "bloqueado",
    "critico",
    "crítico",
    "produccion",
    "producción",
    "todos los usuarios",
    "caido",
    "caído",
)

MEDIUM_TERMS = (
    "iniciar",
    "sesion",
    "sesión",
    "contraseña",
    "password",
    "repetido",
)


def _normalize(message: str) -> str:
    return re.sub(r"\s+", " ", message.lower().strip())


def classify_category(normalized_message: str) -> str:
    score = {
        "ACCESS": sum(term in normalized_message for term in ACCESS_TERMS),
        "BUG": sum(term in normalized_message for term in BUG_TERMS),
        "FEATURE": sum(term in normalized_message for term in FEATURE_TERMS),
        "SECURITY": sum(term in normalized_message for term in SECURITY_TERMS),
    }

    # Security is never downgraded by keywords from another category.
    if score["SECURITY"] > 0:
        return "SECURITY"

    return max(score, key=score.get)


def classify_priority(normalized_message: str, category: str) -> str:
    if category == "SECURITY":
        if any(term in normalized_message for term in CRITICAL_TERMS):
            return "CRITICAL"
        return "HIGH"

    if any(term in normalized_message for term in CRITICAL_TERMS):
        return "CRITICAL"
    if any(term in normalized_message for term in HIGH_TERMS):
        return "HIGH"
    if any(term in normalized_message for term in MEDIUM_TERMS):
        return "MEDIUM"
    if category == "FEATURE":
        return "LOW"
    return "LOW"


def build_response(category: str) -> str:
    responses = {
        "ACCESS": (
            "Lamentamos el inconveniente. Verifique sus credenciales y utilice "
            "la recuperación de contraseña si es necesario."
        ),
        "BUG": (
            "Entendemos la incidencia reportada. Nuestro equipo revisará el error "
            "y solicitará los registros necesarios para reproducirlo."
        ),
        "FEATURE": (
            "Gracias por la sugerencia. Registraremos la solicitud para evaluar "
            "su viabilidad y prioridad dentro del roadmap."
        ),
        "SECURITY": (
            "Gracias por reportar el incidente de seguridad. Preservaremos la "
            "evidencia y nuestro equipo especializado iniciará una revisión."
        ),
    }
    return responses[category]


def analyze_traditional(message: str) -> AnalysisResult:
    normalized = _normalize(message)
    category = classify_category(normalized)
    priority = classify_priority(normalized, category)

    return AnalysisResult(
        category=category,
        priority=priority,
        response=build_response(category),
        requiresHumanReview=(category == "SECURITY"),
        mode="traditional",
    )
