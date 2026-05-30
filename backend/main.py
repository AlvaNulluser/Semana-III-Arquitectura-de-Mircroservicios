import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from google import genai
from openai import OpenAI
import tiktoken
import io
import PIL.Image
from dotenv import load_dotenv
import pypdf

# Cargar variables de entorno
load_dotenv()

def extract_text_from_pdf(content_bytes: bytes) -> str:
    try:
        pdf_file = io.BytesIO(content_bytes)
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        return f"[Error extrayendo texto del PDF: {str(e)}]"

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Claves
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Clientes
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def count_tokens_openai(text: str, model: str = "gpt-3.5-turbo"):
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        return len(text) // 4  # Fallback aproximado

@app.post("/api/chat")
async def chat_endpoint(
    message: str = Form(...),
    provider: str = Form("gemini"),
    files: Optional[List[UploadFile]] = File(None)
):
    file_metadata = []
    contents_gemini = [message]
    full_text_openai = message
    openai_images = []

    # Procesar archivos
    if files:
        for file in files:
            if not file.filename:
                continue
            
            content_bytes = await file.read()
            file_metadata.append({
                "name": file.filename,
                "size": len(content_bytes),
                "type": file.content_type
            })

            # Extraer contenido de texto si es aplicable para reutilizar
            extracted_text = None
            if file.content_type == "application/pdf":
                extracted_text = extract_text_from_pdf(content_bytes)
            elif file.content_type == "text/plain":
                extracted_text = content_bytes.decode('utf-8', errors='ignore')

            # Para Gemini (Multimodal nativo)
            if file.content_type.startswith("image/"):
                img = PIL.Image.open(io.BytesIO(content_bytes))
                contents_gemini.append(img)
            elif file.content_type.startswith("audio/"):
                from google.genai import types
                audio_part = types.Part.from_bytes(data=content_bytes, mime_type=file.content_type)
                contents_gemini.append(audio_part)
            elif file.content_type in ["application/pdf", "text/plain"]:
                contents_gemini.append(f"\n[Contenido del archivo {file.filename}]:\n{extracted_text}")
            
            # Para OpenAI (Multimodal para imágenes, texto para el resto)
            if file.content_type.startswith("image/"):
                import base64
                base64_image = base64.b64encode(content_bytes).decode('utf-8')
                openai_images.append({
                    "base64": base64_image,
                    "mime_type": file.content_type
                })
            elif file.content_type in ["application/pdf", "text/plain"]:
                full_text_openai += f"\n[Archivo: {file.filename}]\n{extracted_text}"

    try:
        if provider == "gemini":
            if not GEMINI_API_KEY:
                raise HTTPException(status_code=400, detail="Gemini API Key no configurada")
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=contents_gemini
            )
            
            res_text = response.text
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

        elif provider == "openai":
            if not openai_client:
                raise HTTPException(status_code=400, detail="OpenAI API Key no configurada")
            
            if openai_images:
                openai_content = [{"type": "text", "text": full_text_openai}]
                for img_info in openai_images:
                    openai_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img_info['mime_type']};base64,{img_info['base64']}"
                        }
                    })
            else:
                openai_content = full_text_openai

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": openai_content}]
            )
            res_text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
        
        else:
            raise HTTPException(status_code=400, detail="Proveedor no soportado")

        return {
            "response": res_text,
            "files": file_metadata,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
