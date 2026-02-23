from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import sqlite3
import uuid
from datetime import datetime, timedelta
import jwt

SECRET_KEY = "IGLESIA_SECRET_2026"
ALGORITHM = "HS256"

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    conn = sqlite3.connect("cloud.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS movimientos (
        uuid TEXT PRIMARY KEY,
        modulo TEXT,
        tipo TEXT,
        tipo_mov TEXT,
        fecha TEXT,
        monto REAL,
        valor_estimado REAL,
        motivo TEXT,
        creado_en TEXT
    )
    """)
    return conn

class Movimiento(BaseModel):
    modulo: str
    tipo: str
    tipo_mov: str
    fecha: str
    monto: float
    valor_estimado: float
    motivo: str

def create_token(username: str):
    payload = {"sub": username, "exp": datetime.utcnow() + timedelta(days=365)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    if form.username == "admin" and form.password == "admin123":
        return {"access_token": create_token(form.username), "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")

@app.post("/movimientos")
def crear_movimiento(mov: Movimiento, token: str = Depends(verify_token)):
    conn = get_db()
    uid = str(uuid.uuid4())
    creado = datetime.utcnow().isoformat()

    conn.execute("""
    INSERT INTO movimientos VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        uid, mov.modulo, mov.tipo, mov.tipo_mov, mov.fecha,
        mov.monto, mov.valor_estimado, mov.motivo, creado
    ))
    conn.commit()
    return {"uuid": uid}

@app.get("/movimientos")
def obtener_movimientos(since: str = "1970-01-01T00:00:00", token: str = Depends(verify_token)):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM movimientos WHERE creado_en > ? ORDER BY creado_en ASC",
        (since,)
    ).fetchall()

    result = []
    for r in rows:
        result.append({
            "uuid": r[0],
            "modulo": r[1],
            "tipo": r[2],
            "tipo_mov": r[3],
            "fecha": r[4],
            "monto": r[5],
            "valor_estimado": r[6],
            "motivo": r[7],
            "creado_en": r[8],
        })
    return result