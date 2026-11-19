# Servidor MCP con herramientas de consulta

import json
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Servidor Laboratorio")

# Fichas técnicas de los equipos del laboratorio
FICHAS_EQUIPOS = {
    "microscopio_barrido": {
        "nombre_oficial": "Microscopio Electrónico de Barrido (SEM-3000)",
        "ubicacion": "Sala Blanca B - Mesón 2",
        "capacidad_maxima": "2 investigadores por turno",
        "consumibles_incluidos": ["Porta-muestras de aluminio", "Cinta de carbono"],
        "estado_operativo": "Operativo (Calibrado)"
    },
    "secuenciador_adn": {
        "nombre_oficial": "Secuenciador Genético de Alto Rendimiento (SeqPro X)",
        "ubicacion": "Laboratorio de Biología Molecular - Cabina 1",
        "capacidad_maxima": "1 investigador por turno",
        "consumibles_incluidos": ["Cartucho de reactivos estándar", "Puntas con filtro"],
        "estado_operativo": "Operativo"
    }
}

HORARIOS_OCUPADOS = {
    "microscopio_barrido": ["2026-11-20 10:00", "2026-11-20 14:00"],
    "secuenciador_adn": ["2026-11-20 09:00"]
}

@mcp.tool()
def obtener_ficha_equipo(equipo: str) -> str:
    """Devuelve la ficha técnica, ubicación y estado operativo de un equipo de laboratorio."""
    equipo_clean = equipo.lower().strip()
    ficha = FICHAS_EQUIPOS.get(equipo_clean)
    if not ficha:
        return json.dumps({"encontrado": False, "mensaje": f"No existe ficha técnica para '{equipo_clean}'."})
    return json.dumps({"encontrado": True, "equipo_id": equipo_clean, "ficha": ficha})

@mcp.tool()
def consultar_horarios(equipo: str, fecha: str) -> str:
    """Consulta los bloques de horarios disponibles y ocupados para un equipo específico."""
    equipo_clean = equipo.lower().strip()
    bloques_del_dia = [f"{fecha} 09:00", f"{fecha} 10:00", f"{fecha} 11:00", f"{fecha} 12:00"]

    ocupados = HORARIOS_OCUPADOS.get(equipo_clean, [])
    disponibles = [b.split(" ")[-1] for b in bloques_del_dia if b not in ocupados]
    ocupados_dia = [o.split(" ")[-1] for o in ocupados if o.startswith(fecha)]

    return json.dumps({
        "equipo": equipo_clean,
        "fecha": fecha,
        "disponibles": disponibles,
        "ocupados": ocupados_dia
    })

@mcp.tool()
def reservar_equipo(equipo: str, fecha: str, bloque: str, usuario: str) -> str:
    """Registra una reserva confirmada para un equipo en una fecha y bloque horario específico."""
    equipo_clean = equipo.lower().strip()
    registro = f"{fecha} {bloque.strip()}"

    if equipo_clean not in HORARIOS_OCUPADOS:
        HORARIOS_OCUPADOS[equipo_clean] = []

    if registro in HORARIOS_OCUPADOS[equipo_clean]:
        return json.dumps({
            "exito": False,
            "mensaje": f"El bloque {registro} ya fue reservado previamente."
        })

    HORARIOS_OCUPADOS[equipo_clean].append(registro)
    return json.dumps({
        "exito": True,
        "codigo_reserva": f"RES-{equipo_clean[:4].upper()}-{bloque.replace(':', '')}",
        "equipo": equipo_clean,
        "fecha": fecha,
        "bloque": bloque,
        "usuario": usuario
    })

if __name__ == "__main__":
    mcp.run(transport="stdio")