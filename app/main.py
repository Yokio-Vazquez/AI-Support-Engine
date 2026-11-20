from fastapi import FastAPI

from app.routes.analyze import router


app = FastAPI(
    title="AI Support Engine",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
