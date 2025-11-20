from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rental.models import Category, Vehicle, UserProfile


class Command(BaseCommand):
    help = "Crea categorías y vehículos de demostración con datos básicos."

    def handle(self, *args, **options):
        # Categorías
        categories = [
            ("SUV", "Deportivos utilitarios, espaciosos y cómodos."),
            ("Sedán", "Vehículos cómodos para ciudad y viajes."),
            ("Compacto", "Eficientes y fáciles de parquear."),
        ]
        cat_objs = {}
        for name, desc in categories:
            obj, _ = Category.objects.get_or_create(name=name, defaults={"description": desc})
            cat_objs[name] = obj

        # Admin/Operador demo si no existen
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_user("admin", password="admin123", first_name="Admin", last_name="Demo")
            UserProfile.objects.create(user=admin, role="admin")
            self.stdout.write(self.style.SUCCESS("Usuario admin creado: admin/admin123"))

        if not User.objects.filter(username="operador").exists():
            op = User.objects.create_user("operador", password="operador123", first_name="Operador", last_name="Demo")
            UserProfile.objects.create(user=op, role="operador")
            self.stdout.write(self.style.SUCCESS("Usuario operador creado: operador/operador123"))

        # Vehículos demo
        demo_vehicles = [
            {
                "license_plate": "ABC123",
                "brand": "Toyota",
                "model": "RAV4",
                "year": 2021,
                "category": cat_objs["SUV"],
                "transmission": "automatica",
                "daily_rate": 180,
                "capacity": 5,
                "status": "disponible",
                "description": "SUV confiable ideal para familias.",
            },
            {
                "license_plate": "XYZ789",
                "brand": "Honda",
                "model": "Civic",
                "year": 2020,
                "category": cat_objs["Sedán"],
                "transmission": "manual",
                "daily_rate": 140,
                "capacity": 5,
                "status": "disponible",
                "description": "Sedán eficiente y cómodo para ciudad.",
            },
            {
                "license_plate": "JKL456",
                "brand": "Kia",
                "model": "Picanto",
                "year": 2019,
                "category": cat_objs["Compacto"],
                "transmission": "automatica",
                "daily_rate": 100,
                "capacity": 4,
                "status": "disponible",
                "description": "Compacto ágil y económico.",
            },
        ]

        created = 0
        for data in demo_vehicles:
            if not Vehicle.objects.filter(license_plate=data["license_plate"]).exists():
                Vehicle.objects.create(**data)
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Vehículos creados: {created}"))
        self.stdout.write(self.style.SUCCESS("Listo. Puedes verlos en /vehiculos o gestionarlos en el dashboard."))