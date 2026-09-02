class ProviderError(Exception):
    """El proveedor de IA falló (sin clave, límite de cuota, red, error del servicio).
    El orquestador la captura para pasar al siguiente proveedor o, si se acaban,
    disparar el mensaje de transferencia a un humano."""
