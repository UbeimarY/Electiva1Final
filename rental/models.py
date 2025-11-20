from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime


class Category(models.Model):
    """Modelo para categorías de vehículos"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    """Modelo para vehículos"""
    TRANSMISSION_CHOICES = [
        ('manual', 'Manual'),
        ('automatica', 'Automática'),
    ]

    STATUS_CHOICES = [
        ('disponible', 'Disponible'),
        ('alquilado', 'Alquilado'),
        ('mantenimiento', 'En Mantenimiento'),
    ]

    license_plate = models.CharField(max_length=20, unique=True, verbose_name="Placa")
    brand = models.CharField(max_length=100, verbose_name="Marca")
    model = models.CharField(max_length=100, verbose_name="Modelo")
    year = models.IntegerField(verbose_name="Año")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Categoría")
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, verbose_name="Transmisión")
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tarifa Diaria")
    capacity = models.IntegerField(verbose_name="Capacidad de Pasajeros")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponible', verbose_name="Estado")
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True, verbose_name="Imagen")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"

    def clean(self):
        """Validaciones personalizadas"""
        if self.year > datetime.now().year + 1:
            raise ValidationError({'year': 'El año no puede ser mayor al año siguiente.'})
        if self.daily_rate <= 0:
            raise ValidationError({'daily_rate': 'La tarifa debe ser mayor a 0.'})


class UserProfile(models.Model):
    """Extensión del modelo User para roles"""
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('cliente', 'Cliente'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cliente', verbose_name="Rol")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    address = models.TextField(blank=True, verbose_name="Dirección")
    identification = models.CharField(max_length=50, blank=True, verbose_name="Identificación")

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class Rental(models.Model):
    """Modelo para alquileres"""
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    client = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rentals', verbose_name="Cliente")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='rentals', verbose_name="Vehículo")
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(verbose_name="Fecha de Devolución")
    days = models.IntegerField(verbose_name="Días")
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tarifa Diaria")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Total")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente', verbose_name="Estado")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Alquiler"
        verbose_name_plural = "Alquileres"
        ordering = ['-created_at']

    def __str__(self):
        return f"Alquiler #{self.id} - {self.vehicle} - {self.client.get_full_name()}"

    def clean(self):
        """Validaciones personalizadas"""
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError({'end_date': 'La fecha de devolución debe ser posterior a la fecha de inicio.'})
            
            # Verificar solapamiento de fechas
            overlapping = Rental.objects.filter(
                vehicle=self.vehicle,
                status__in=['pendiente', 'activo']
            ).exclude(pk=self.pk).filter(
                models.Q(start_date__lte=self.end_date) & models.Q(end_date__gte=self.start_date)
            )
            
            if overlapping.exists():
                raise ValidationError('El vehículo ya está reservado en estas fechas.')

    def save(self, *args, **kwargs):
        """Calcular días y monto total antes de guardar"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.days = delta.days + 1
            self.total_amount = self.days * self.daily_rate
        super().save(*args, **kwargs)
