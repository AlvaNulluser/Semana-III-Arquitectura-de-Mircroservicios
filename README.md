# Chatbot Inteligente con Gemini

Este proyecto implementa un chatbot inteligente que integra frontend (HTML/CSS/JS) con backend en Python usando FastAPI y Gemini de Google.

## Requisitos

- Python 3.8+
- API Key de Google Gemini

## Instalación

1. Crear entorno virtual (asegúrate de estar en la carpeta raíz `chatbot_project`):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Instalar dependencias:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Configurar API Key:
   - Edita `backend/.env` y agrega tu `GEMINI_API_KEY`

## Ejecución

1. Iniciar el backend (con el entorno virtual activado):
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```
   El backend estará disponible en http://localhost:8000

2. Abrir el frontend:
   - Abre `frontend/index.html` en tu navegador web.
   - O usa un servidor local: `cd frontend && python3 -m http.server 3000`
   - Luego abre http://localhost:3000

## Funcionalidades

- Envío de mensajes de texto
- Subida de archivos (imágenes, audio, documentos)
- Respuestas generadas por Gemini
- Renderizado de código con resaltado de sintaxis
- Selector de temas (claro, oscuro, personalizado)
- Visualización del consumo de tokens

## Estructura del Proyecto

```
chatbot_project/
├── .gitignore
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── index.html
    ├── styles.css
    └── script.js
```