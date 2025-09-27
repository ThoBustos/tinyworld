from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TinyWorld API",
    description="A tiny autonomous world simulation backend",
    version="0.1.0"
)

# Add CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to TinyWorld API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
