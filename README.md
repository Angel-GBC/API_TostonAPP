# API - TostonAPP

API construida con FastAPI, SQLAlchemy y MySQL.

## Requisitos
- Python 3.11+
- MySQL

## Instalacion
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

## Configuracion
Copia `.env` y completa tus datos de conexion a MySQL.

## Ejecutar
```bash
uvicorn src.main:app --reload
```

Documentacion automatica: http://localhost:8000/docs
