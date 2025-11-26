# TimeWise API

API REST para la app TimeWise usando **FastAPI + SQLite**.

## Estructura

app/routes/models.py
app/database/create-timewise.sql
app/app.py


## Iniciar
```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd app
cd ..
uvicorn app.app:app --reload
```
Endpoints

POST /auth/register → Registro
POST /auth/login → Login (JWT)
Documentación: http://localhost:8000/docs


---

## 9. `ApiDocumentation.MD`

```md
# Documentación API TimeWise

## Auth
- `POST /auth/register` → `{correo, contrasena, nombres, apellidos}`
- `POST /auth/login` → `{username, password}` → JWT

## Próximos
- `/tareas/` → CRUD de tareas
- `/estadisticas/` → Reportes
- `/metas/` → Metas personales