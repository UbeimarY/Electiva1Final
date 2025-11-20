# Sistema de Alquiler de Vehículos (RentCar)

## Características
- Autenticación y roles (`admin`, `operador`, `cliente`)
- CRUD de vehículos y categorías, reservas y administración de alquileres
- Dashboard con métricas y gráficos (Chart.js)
- Exportación de datos: CSV y Excel
- Contrato de alquiler descargable en PDF
- Filtros de búsqueda por texto, estado y fechas
- Interfaz responsiva con Bootstrap 5

## Instalación
1. Crear entorno y dependencias:
   - `pip install -r requirements.txt`
2. Migraciones y datos:
   - `python manage.py migrate`
   - `python manage.py shell` y ejecutar `exec(open('scripts/create_test_data.py').read())`
3. Ejecutar:
   - `python manage.py runserver`

## Despliegue (Render/Heroku)
- Variables:
  - `DEBUG=False`
  - `ALLOWED_HOSTS=yourdomain.com`
  - `DATABASE_URL=postgres://...` (PostgreSQL)
- Comandos:
  - Build: `pip install -r requirements.txt`
  - Start: `gunicorn vehiclerental.wsgi`
- Estáticos: `python manage.py collectstatic`

## Endpoints principales
- `/` inicio, `/login`, `/register`
- `/vehicles` listado de vehículos
- `/dashboard` administración
- `/dashboard/rentals/export` CSV
- `/dashboard/rentals/export/xlsx` Excel
- `/dashboard/rentals/contract/<id>` Contrato PDF

## Notas
- Para PostgreSQL se usa `dj-database-url` y `TruncMonth` para ingresos mensuales.
- Se requiere `Pillow` para `ImageField`.