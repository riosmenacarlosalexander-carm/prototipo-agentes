# Instrucciones de instalación y ejecución

## Sistema de Gestión de Reservas con Agentes (MCP + RAG)

Este repositorio contiene el prototipo funcional para la reserva automatizada de equipos de laboratorio utilizando la arquitectura **Model Context Protocol (MCP)**, inyección de contexto documental (**RAG**) y ciclos de control de aprobación.

### Requisitos Previos

* Python 3.10 o superior instalado en el sistema.

### Instalación y Configuración

1. Clone este repositorio o extraiga el archivo comprimido.
2. Abra una terminal en la raíz del proyecto.
3. Instale la dependencia del SDK de MCP ejecutando:
   ```bash pip install -r requirements.txt```

### Ejecución del Prototipo

Para iniciar el ciclo completo del agente (el cual lanzará automáticamente el servidor MCP de forma interna para interactuar), ejecute:
```bash python agente_laboratorio.py```

*Nota: No se requieren configurar variables de entorno ni `API_KEYS` de proveedores externos debido a que las capas de embedding, almacenamiento y herramientasse ejecutan de manera local y determinista para fines de demostración académica.*
