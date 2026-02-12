from fastapi import FastAPI
from api.routes import router as generate_router


import logging
logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s "
    )
)


app = FastAPI()

app.include_router(generate_router)
