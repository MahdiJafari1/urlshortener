import hashlib

import sqlalchemy
from fastapi import Depends, FastAPI
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

app = FastAPI()

# Database setup
DATABASE_URL = "sqlite:///./urls.db"
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class URLItem(BaseModel):
    url: HttpUrl


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


@app.post("/shorten_url")
def create_short_url(item: URLItem, db: Session = Depends(get_db)):
    """Gets a long URL and return its short URL."""
    long_url = item.url

    key = generate_short_key(long_url)

    # Check for duplicate key and re-hash if necessary
    while db.query(URL).filter(URL.key == key).first():
        key = generate_short_key(key + "1")

    url = URL(key=key, long_url=long_url)
    db.add(url)
    db.commit()

    short_url = f"http://localhost:8000/{key}"
    response = {"short_url": short_url}

    return response


@app.get("/{key}")
def redirect_short_url(key: str, db: Session = Depends(get_db)):
    """Redirects to the long URL."""
    url = db.query(URL).filter(URL.key == key).first()

    if url:
        long_url = url.long_url
        return RedirectResponse(url=long_url, status_code=302)
    else:
        return PlainTextResponse("URL not found", status_code=404)


@app.delete("/{key}")
def delete_short_url(key: str, db: Session = Depends(get_db)):
    """Remove the short URL from the database."""
    url = db.query(URL).filter(URL.key == key).first()

    if url:
        db.delete(url)
        db.commit()
        return {"message": "URL deleted"}
    else:
        return PlainTextResponse("URL not found", status_code=404)


def generate_short_key(long_url):
    """Generate a short key for the long URL."""
    return hashlib.md5(long_url.encode()).hexdigest()[:6]
