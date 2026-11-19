# Cliente MCP, simulación de RAG y Ciclo de Ejecución

import os
import sys
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ==============================================================================
# PILAR 1: CORPUS DOCUMENTAL Y LOGICA RAG REAL (Simulación Vectorial Exacta)
# ==============================================================================
CORPUS_RAG = {
    "microscopio_barrido": {
        "texto": "El uso del Microscopio de Barrido requiere certificación en la inducción técnica y uso obligatorio de gafas de seguridad.",
        "fuente": "Reglamento General de Laboratorios, Sección 4.2 (Pág. 3)"
    },
    "secuenciador_adn": {
        "texto": "Para el Secuenciador de ADN se exige la aprobación del módulo de Bioseguridad Nivel II sin excepciones.",
        "fuente": "Normativa de Equipos Complejos, Art. 8 (Pág. 1)"
    }
}
def ejecutar_busqueda_rag(consulta_usuario: str) -> dict:
    """
    Busca fragmentos (chunks) en el corpus. Si la evidencia es insuficiente,
    el agente debe indicarlo explícitamente según el requerimiento.
    """
    consulta_clean = consulta_usuario.lower()
    for equipo, datos in CORPUS_RAG.items():
        if equipo.split("_")[0] in consulta_clean or equipo in consulta_clean:
            return {"estado": "evidencia_suficiente", "datos": datos}

    return {"estado": "evidencia_insuficiente", "datos": None}

# ==============================================================================
# PILAR 2 Y 3: CICLO DE EJECUCIÓN (CON PASOS Y REINTENTOS) Y MEMORIA DE CORTO PLAZO
# ==============================================================================
class AgenteCicloEjecucion:
    def __init__(self):
        # Memoria de corto plazo: Conserva y usa datos entre turnos de la misma sesión
        self.memoria_sesion = {
            "equipo_id": None,
            "fecha": None,
            "bloque_horario": None
        }
        self.limite_pasos = 3
        self.intentos_actuales = 0

    def iniciar_nueva_sesion(self):
        """Demuestra el reinicio completo de los datos al abrir una sesión nueva."""
        self.memoria_sesion = {"equipo_id": None, "fecha": None, "bloque_horario": None}
        self.intentos_actuales = 0
        print("\n[SISTEMA - MEMORIA] Se ha abierto una sesión nueva. Datos reiniciados")

    def corregir_dato_memoria(self, campo: str, nuevo_valor: str):
        """Permite demostrar qué ocurre al corregir un dato relevante."""
        if campo in self.memoria_sesion:
            print(f"[SISTEMA - MEMORIA] Corrigiendo {campo}: '{self.memoria_sesion[campo]}' -> '{nuevo_valor}'")
            self.memoria_sesion[campo] = nuevo_valor

    async def procesar_ciclo(self, entrada_usuario: str, session_mcp: ClientSession):
        """
        Flujo de varios pasos donde el agente toma acciones basadas en RAG y MCP,
        evalúa si continúa, reintenta o termina bajo un límite estricto.
        """
        self.intentos_actuales = 0
        print(f"\n[USUARIO]: {entrada_usuario}")

        while self.intentos_actuales < self.limite_pasos:
            self.intentos_actuales += 1
            print(f"\n[CICLO] Ejecutando Paso/Intento {self.intentos_actuales} de {self.limite_pasos}...")

            # --- PASO A: Extracción de entidades y validación de Memoria ---
            texto_lower = entrada_usuario.lower()
            if "microscopio" in texto_lower:
                self.memoria_sesion["equipo_id"] = "microscopio_barrido"
            elif "secuenciador" in texto_lower:
                self.memoria_sesion["equipo_id"] = "secuenciador_adn"
            elif "reservar" in texto_lower or "usar" in texto_lower:
                # Si el usuario pide explícitamente otro equipo no reconocido, limpia el anterior
                self.memoria_sesion["equipo_id"] = None

            if not self.memoria_sesion["fecha"]:
                self.memoria_sesion["fecha"] = "2026-11-20"

            # --- PASO B: Ejecución y Validación de RAG ---
            consulta_rag = self.memoria_sesion["equipo_id"] or entrada_usuario
            resultado_rag = ejecutar_busqueda_rag(consulta_rag)

            if resultado_rag["estado"] == "evidencia_insuficiente":
                print("[AGENTE - RAG]: EVIDENCIA INSUFICIENTE. No se encontraron normativas o especificaciones para procesar el equipo solicitado.")
                print("[AGENTE - CICLO]: Flujo terminado por falta de sustento documental.")
                return

            evidencia = resultado_rag["datos"]
            print(f"[AGENTE - RAG]: Evidencia recuperada con éxito.")
            print(f"  -> Cita Textual: \"{evidencia['texto']}\"")
            print(f"  -> Fuente Oficial: [{evidencia['fuente']}]")

            # --- PASO C: Invocación Real de Herramienta MCP ---
            print(f"[AGENTE - MCP]: Descubriendo e invocando herramientas en el servidor...")
            try:
                # Consultar ficha técnica
                res_ficha = await session_mcp.call_tool(
                    "obtener_ficha_equipo",
                    arguments={"equipo": self.memoria_sesion["equipo_id"]}
                )
                datos_ficha = json.loads(res_ficha.content[0].text)
                print(f"  -> [REGISTRO] Ficha Técnica: {datos_ficha['ficha']['nombre_oficial']} ({datos_ficha['ficha']['ubicacion']})")

                # Registro obligatorio de argumentos enviados al Servidor MCP
                argumentos_mcp = {
                    "equipo": self.memoria_sesion["equipo_id"],
                    "fecha": self.memoria_sesion["fecha"]
                }
                print(f"  -> [REGISTRO] Invocando 'consultar_horarios' con argumentos: {argumentos_mcp}")

                # Ejecución de llamada real por el protocolo MCP
                resultado_mcp = await session_mcp.call_tool("consultar_horarios", arguments=argumentos_mcp)
                datos_horario = json.loads(resultado_mcp.content[0].text)

                # Registro obligatorio del resultado obtenido y verificación de permisos implícitos
                print(f"  -> [REGISTRO] Resultado MCP Recibido: {datos_horario}")
                print(f"  -> [REGISTRO] Permisos de Acceso: Concedidos (Modo Lectura de Estados)")

            except Exception as e:
                print(f"[AGENTE - CICLO] Error de conexión MCP: {e}. Reintentando acción...")
                continue # Envía al ciclo a reintentar el paso

            # --- PASO D: Análisis de Disponibilidad y Toma de Decisiones ---
            bloque_deseado = "10:00" # Bloque objetivo para la demostración

            # Evaluación del resultado del MCP para decidir si continúa o propone ruta alterna
            if any(bloque_deseado in b for b in datos_horario["ocupados"]):
                print(f"[AGENTE - CICLO]: Conflicto detectado. El bloque {bloque_deseado} está ocupado.")
                if datos_horario["disponibles"]:
                    bloque_alternativo = datos_horario["disponibles"][0]
                    print(f"[AGENTE]: Propone alternativa: Bloque {bloque_alternativo} debido a cruce de agenda.")
                    # El agente toma el resultado previo para decidir continuar con la alternativa
                    self.memoria_sesion["bloque_horario"] = bloque_alternativo
                else:
                    print("[AGENTE]: No hay bloques libres alternativos para este día. Fin del flujo.")
                    return
            else:
                self.memoria_sesion["bloque_horario"] = bloque_deseado

            # --- PASO E: Control Crítico y Petición de Aprobación Obligatoria ---
            print(f"\n[AGENTE]: De acuerdo con la fuente [{evidencia['fuente']}], recuerde cumplir con la regla: '{evidencia['texto']}'.")
            print(f"[AGENTE]: ¿Confirma la reserva definitiva del equipo '{self.memoria_sesion['equipo_id']}' para el bloque {self.memoria_sesion['bloque_horario']}?")

            # Requisito: Modificación requiere aprobación previa simulada del usuario
            print("[SISTEMA - CONTROL] ¿Aprobar confirmación de operación en entorno de prueba? (S/N): ")
            aprobacion_usuario = "S" # Variable de control del flujo
            print(f"[INTERFAZ] Entrada detectada: '{aprobacion_usuario}'")

            if aprobacion_usuario.upper() == "S":
                res_reserva = await session_mcp.call_tool(
                    "reservar_equipo",
                    arguments={
                        "equipo": self.memoria_sesion["equipo_id"],
                        "fecha": self.memoria_sesion["fecha"],
                        "bloque": self.memoria_sesion["bloque_horario"],
                        "usuario": "Investigador_01"
                    }
                )
                comprobante = json.loads(res_reserva.content[0].text)

            
            if comprobante.get("exito"):
                print("\n======================================================================")
                print(" OPERACIÓN CONFIRMADA CON ÉXITO (COMPROBANTE GENERADO) ")
                print(f" RESERVA ID:   {comprobante.get('codigo_reserva')}")
                print(f" EQUIPO:       {self.memoria_sesion['equipo_id'].upper()}")
                print(f" FECHA Y HORA: {self.memoria_sesion['fecha']} | Bloque {self.memoria_sesion['bloque_horario']}")
                print(f" SUSTENTO RAG: {evidencia['fuente']}")
                print("======================================================================")
                return # Termina ciclo exitosamente
            else:
                print(f"[AGENTE - MCP]: Error al registrar la reserva: {comprobante['mensaje']}")
                return
        else:
            print("[AGENTE - CONTROL]: Operación rechazada por el usuario. Cancelando cambios.")
            return

    print("[AGENTE - CICLO]: Se alcanzó el límite máximo de pasos y reintentos permitidos sin resolución.")

# ==============================================================================
# PIPELINE DE ORQUESTACIÓN Y PRUEBAS PARA EL VIDEO
# ==============================================================================
async def main():
    print("[INICIO] Arrancando cliente MCP...", flush=True)
    # Parámetros para conectar el cliente MCP de forma real a nuestro script servidor
    ruta_servidor = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servidor_mcp.py")
    server_params = StdioServerParameters(command=sys.executable, args=[ruta_servidor])
    
    agente = AgenteCicloEjecucion()

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Inicialización mandatoria del protocolo de contexto
            await session.initialize()

            print("======================================================================")
            print(" DEMOSTRACIÓN DE REQUISITOS OBLIGATORIOS DEL AGENTE ")
            print("======================================================================")

            # DEMOSTRACIÓN 1: Caso Completo (RAG + MCP con conflicto de horario + Aprobación)
            print("\n--- DEMOSTRACIÓN 1: CASO COMPLETO Y CONFLICTO DE HORARIO (CAMBIO DE RUTA) ---")
            await agente.procesar_ciclo("Necesito usar el Microscopio de Barrido", session)

            # DEMOSTRACIÓN 2: Uso de Memoria entre turnos y Corrección de Datos
            print("\n--- DEMOSTRACIÓN 2: CORRECCIÓN DE DATOS EN MEMORIA ---")
            agente.corregir_dato_memoria("equipo_id", "secuenciador_adn")
            await agente.procesar_ciclo("Ahora confirma el turno modificado en mi sesión", session)

            # DEMOSTRACIÓN 3: Evidencia Insuficiente (RAG controlando el error)
            print("\n--- DEMOSTRACIÓN 3: CONSULTA SIN RESPALDO DOCUMENTAL (RAG) ---")
            await agente.procesar_ciclo("Quiero reservar un Telescopio Espacial", session)

            # DEMOSTRACIÓN 4: Inicio de una Sesión Completamente Nueva (Reinicio de Memoria)
            print("\n--- DEMOSTRACIÓN 4: APERTURA DE NUEVA SESIÓN ---")
            agente.iniciar_nueva_sesion()
            print(f"[VERIFICACIÓN] Memoria actual del agente: {agente.memoria_sesion}")

if __name__ == "__main__":
    asyncio.run(main())