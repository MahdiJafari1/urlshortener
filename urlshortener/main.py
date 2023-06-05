import hashlib

import sqlalchemy
from fastapi import Depends, FastAPI
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

app = FastAPI()

# Database setup
DATABASE_URL = "sqlite:///./urls.db"
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class URLItem(BaseModel):
    url: str


class URL(Base):
    __tablename__ = "urls"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    key = sqlalchemy.Column(sqlalchemy.String(10), unique=True, index=True)
    long_url = sqlalchemy.Column(sqlalchemy.String)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/")
def create_short_url(item: URLItem, db: Session = Depends(get_db)):
    long_url = item.url

    # Generate a short key (hash) for the URL
    key = generate_short_key(long_url)

    # Check for duplicate key and re-hash if necessary
    while db.query(URL).filter(URL.key == key).first():
        key = generate_short_key(key + "1")  # Add a unique value and re-hash

    url = URL(key=key, long_url=long_url)
    db.add(url)
    db.commit()

    # Construct the response
    short_url = f"http://localhost/{key}"
    response = {"key": key, "long_url": long_url, "short_url": short_url}

    return response


@app.get("/{key}")
def redirect_short_url(key: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.key == key).first()

    if url:
        long_url = url.long_url
        return RedirectResponse(url=long_url, status_code=302)
    else:
        return PlainTextResponse("URL not found", status_code=404)


@app.delete("/{key}")
def delete_short_url(key: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.key == key).first()

    if url:
        db.delete(url)
        db.commit()
        return {"message": "URL deleted"}
    else:
        return PlainTextResponse("URL not found", status_code=404)


def generate_short_key(long_url):
    # Implement your hash function or use an existing library to generate a short key
    # Make sure to consider collision probability when deciding on the key length
    # For simplicity, we'll use a basic hash of the URL here
    return hashlib.md5(long_url.encode()).hexdigest()[:6]
