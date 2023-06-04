from fastapi import FastAPI

app = FastAPI()


@app.route('/')
async def index():
    return {'hello, FastAPI!'}

