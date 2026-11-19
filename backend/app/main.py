import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import configuracao
from .routers import solicitacoes, triagem

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="Cidade Atende API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracao.origens_permitidas,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(triagem.router)
app.include_router(solicitacoes.router)


@app.exception_handler(RequestValidationError)
async def erro_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
    campos = [{"campo": ".".join(str(p) for p in e["loc"][1:]), "mensagem": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"erro": "entrada_invalida", "campos": campos})


@app.exception_handler(Exception)
async def erro_inesperado(_: Request, exc: Exception) -> JSONResponse:
    log.exception("erro inesperado: %s", exc)
    return JSONResponse(status_code=500, content={"erro": "erro_interno"})
