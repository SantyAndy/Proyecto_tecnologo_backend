# Proyecto_tecnologo_backend

API REST (Django + DRF) del sistema de monitoreo del café.

## Puesta en marcha

1. Crea el entorno e instala dependencias:
   ```bash
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt
   ```
2. Copia `.env.example` como `.env` y complétalo (clave secreta, contraseña de
   PostgreSQL, correo de Gmail con contraseña de aplicación). **El `.env` nunca
   se sube a git.**
3. `venv\Scripts\python manage.py migrate`
4. `venv\Scripts\python manage.py runserver 0.0.0.0:8000`

## Seguridad

- **Credenciales**: solo en el `.env`. Si `DJANGO_SECRET_KEY` o `DB_PASSWORD`
  faltan, el servidor no arranca.
- **Producción**: `DJANGO_DEBUG=False` y `DJANGO_ALLOWED_HOSTS` con el dominio
  real. Se activan HTTPS obligatorio, HSTS y cookies seguras.
- **Límites de peticiones**: login, registro, recuperación de contraseña,
  contacto, ingesta y análisis IA tienen un máximo por minuto u hora
  (`DEFAULT_THROTTLE_RATES` en `config/settings.py`).
- **Arduinos**: cada dispositivo tiene una clave secreta. El Arduino debe
  enviarla en la cabecera `X-Arduino-Key` al hacer `POST /api/ingesta/`; sin
  ella la lectura se rechaza (403).

## Conectar un Arduino

1. Corre Django escuchando en la red: `python manage.py runserver 0.0.0.0:8000`
   (con `runserver` a secas el Arduino no puede conectarse). Permite Python en
   el Firewall de Windows para el puerto 8000.
2. En la página entra a **Dispositivos**, registra el Arduino y pulsa
   **Código Arduino**: escribe la red WiFi y la IP del servidor y descarga el
   `.ino` ya configurado (ID y clave incluidos).
3. Cárgalo con el Arduino IDE. En el Monitor Serie (115200 baudios) verás cada
   envío; en la página el estado pasará a **En línea**.

Formato que envía el Arduino:

```
POST /api/ingesta/
X-Arduino-Key: <clave del dispositivo>
Content-Type: application/json

{"arduino_id": 1, "ph": 6.2, "humedad_suelo": 41.5, "temperatura": 21.3, "humedad_aire": 68}
```

Rangos aceptados: pH 0–14, humedades 0–100 %, temperatura −40–85 °C. Un campo
que no se envía se guarda como "sin dato".

API de dispositivos (usuario autenticado): `GET/POST /api/dispositivos/`,
`PATCH/DELETE /api/dispositivos/<id>/`, `POST /api/dispositivos/<id>/regenerar-clave/`,
`GET /api/dispositivos/conexion/` (IPs de este computador).

- Pruebas de seguridad: `venv\Scripts\python manage.py test tablas.tests_seguridad`
