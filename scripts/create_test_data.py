"""
Script alternativo para crear datos de prueba
Ejecutar con: python manage.py shell
Luego: exec(open('scripts/create_test_data.py').read())
"""

from django.contrib.auth.models import User
from rental.models import Category, Vehicle, UserProfile
from datetime import datetime

print("Creando datos de prueba...")

# Crear categorías
categories = {
    'SUV': Category.objects.get_or_create(
        name='SUV',
        defaults={'description': 'Vehículos todoterreno espaciosos'}
    )[0],
    'Sedán': Category.objects.get_or_create(
        name='Sedán',
        defaults={'description': 'Automóviles elegantes y cómodos'}
    )[0],
    'Compacto': Category.objects.get_or_create(
        name='Compacto',
        defaults={'description': 'Vehículos pequeños y económicos'}
    )[0],
}

print(f"✓ Creadas {len(categories)} categorías")

# Crear usuario admin si no existe
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@rental.com',
        password='admin123',
        first_name='Admin',
        last_name='Sistema'
    )
    UserProfile.objects.create(user=admin, role='admin', phone='+1234567890')
    print("✓ Usuario admin creado (admin/admin123)")

# Crear usuario cliente
if not User.objects.filter(username='cliente').exists():
    cliente = User.objects.create_user(
        username='cliente',
        email='cliente@example.com',
        password='cliente123',
        first_name='María',
        last_name='García'
    )
    UserProfile.objects.create(
        user=cliente,
        role='cliente',
        phone='+1234567892',
        address='Calle Principal 123',
        identification='CLI-001'
    )
    print("✓ Usuario cliente creado (cliente/cliente123)")

# Crear vehículos de ejemplo
vehicles_data = [
    ('ABC-123', 'Toyota', 'RAV4', 2023, 'SUV', 'automatica', 85.00, 5),
    ('DEF-456', 'Honda', 'Civic', 2022, 'Sedán', 'automatica', 65.00, 5),
    ('GHI-789', 'Chevrolet', 'Spark', 2021, 'Compacto', 'manual', 35.00, 4),
]

for plate, brand, model, year, cat_name, trans, rate, cap in vehicles_data:
    Vehicle.objects.get_or_create(
        license_plate=plate,
        defaults={
            'brand': brand,
            'model': model,
            'year': year,
            'category': categories[cat_name],
            'transmission': trans,
            'daily_rate': rate,
            'capacity': cap,
            'status': 'disponible',
            'description': f'{brand} {model} en excelente estado'
        }
    )

print(f"✓ Creados {len(vehicles_data)} vehículos")
print("\n¡Datos de prueba cargados exitosamente!")
print("Accede con: admin/admin123 o cliente/cliente123")
