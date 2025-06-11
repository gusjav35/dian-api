from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse, Response
import abrir_dian
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = FastAPI()

@app.get("/consultar")
async def consultar(request: Request, nit: str = Query(...)):
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header != API_KEY:
        raise HTTPException(status_code=401, detail="No autorizado: clave inválida")

    if os.path.exists("resultado_dian.json"):
        os.remove("resultado_dian.json")

    # ✅ quitar await porque main() no es async
    abrir_dian.main(nit)

    try:
        with open("resultado_dian.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        if "error" in data and data["error"]:
            return JSONResponse(status_code=422, content=data)

        return JSONResponse(content=data)

    except Exception as e:
        return JSONResponse(content={"error": f"No se pudo leer el archivo JSON: {str(e)}"})

@app.get("/favicon.ico")
async def favicon():
    return Response(content="", media_type="image/x-icon")

@app.get("/")
@app.head("/")
def root():
    return {"mensaje": "API DIAN funcionando correctamente ✅"}
