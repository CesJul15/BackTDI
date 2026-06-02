Demo backend — Generación de muestras con Hugging Face

Pasos rápidos para preparar la demo local:

1. Variables de entorno (`backend/.env`)

REQUIRED:

- `HF_TOKEN` — tu token de Hugging Face

OPTIONAL:

- `HF_MODEL` — modelo de HF (por defecto `facebook/musicgen-small`)

2. Instalar dependencias y migrar

```bash
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

3. Crear un admin de demo (opcional)

```bash
python manage.py crear_admin --username demo --email demo@example.com --password demo123
```

4. Pre-generar muestras para todos los instrumentos

```bash
python manage.py generar_muestras
# O forzar sobrescritura
python manage.py generar_muestras --force
```

5. Ejecutar servidor y probar en el frontend

```bash
python manage.py runserver
# en otra terminal
cd frontend
npm run dev
```

Notas:
- El endpoint que genera audio desde la vista de detalle es `POST /api/instrumentos/<id>/generate_audio/` y requiere autenticación.
- Para la demo puedes usar `generar_muestras` para generar archivos antes de presentar y así evitar latencia en vivo.
