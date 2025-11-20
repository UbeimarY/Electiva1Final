from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from django.template.loader import render_to_string
from django.conf import settings
import os
from io import BytesIO
from django.db.models.functions import TruncMonth

from .models import Vehicle, Category, Rental, UserProfile
from .forms import (
    UserRegistrationForm, VehicleForm, CategoryForm, 
    RentalForm, RentalFilterForm, RentalUpdateForm
)


def home(request):
    """Vista principal"""
    vehicles = Vehicle.objects.filter(status='disponible')[:6]
    categories = Category.objects.all()
    context = {
        'vehicles': vehicles,
        'categories': categories,
    }
    return render(request, 'rental/home.html', context)


def register_view(request):
    """Vista de registro"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso! Bienvenido.')
            return redirect('vehicles_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'rental/register.html', {'form': form})


def login_view(request):
    """Vista de login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirigir según el rol
            profile = getattr(user, 'profile', None)
            if profile and profile.role in ['admin', 'operador']:
                return redirect('dashboard')
            return redirect('vehicles_list')
        else:
            messages.error(request, 'Credenciales inválidas.')
    
    return render(request, 'rental/login.html')


def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('home')


@login_required
def vehicles_list(request):
    """Lista de vehículos para clientes"""
    vehicles = Vehicle.objects.filter(status='disponible')
    categories = Category.objects.all()
    
    # Filtros
    category_id = request.GET.get('category')
    search = request.GET.get('search')
    transmission = request.GET.get('transmission')
    
    if category_id:
        vehicles = vehicles.filter(category_id=category_id)
    if search:
        vehicles = vehicles.filter(
            Q(brand__icontains=search) | 
            Q(model__icontains=search) |
            Q(license_plate__icontains=search)
        )
    if transmission:
        vehicles = vehicles.filter(transmission=transmission)
    
    context = {
        'vehicles': vehicles,
        'categories': categories,
    }
    return render(request, 'rental/vehicles_list.html', context)


@login_required
def rental_create(request, vehicle_id):
    """Crear nueva reserva"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, status='disponible')
    
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save(commit=False)
            rental.client = request.user
            rental.daily_rate = vehicle.daily_rate
            # Calcular días y monto antes de validar, para evitar errores de campos nulos
            try:
                if rental.start_date and rental.end_date:
                    delta = rental.end_date - rental.start_date
                    rental.days = delta.days + 1
                    rental.total_amount = rental.days * rental.daily_rate
            except Exception:
                pass
            
            try:
                rental.full_clean()
                rental.save()
                
                # Actualizar estado del vehículo
                vehicle.status = 'alquilado'
                vehicle.save()
                
                messages.success(request, '¡Reserva creada exitosamente!')
                return redirect('my_rentals')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = RentalForm(initial={'vehicle': vehicle})
    
    context = {
        'form': form,
        'vehicle': vehicle,
    }
    return render(request, 'rental/rental_create.html', context)


@login_required
def my_rentals(request):
    """Mis reservas (cliente)"""
    rentals = Rental.objects.filter(client=request.user).order_by('-created_at')
    context = {'rentals': rentals}
    return render(request, 'rental/my_rentals.html', context)


@login_required
def rental_edit_user(request, pk):
    """Editar una reserva propia (solo pendiente)"""
    rental = get_object_or_404(Rental, pk=pk, client=request.user)

    if rental.status != 'pendiente':
        messages.error(request, 'Solo puedes editar reservas en estado pendiente.')
        return redirect('my_rentals')

    if request.method == 'POST':
        form = RentalUpdateForm(request.POST, instance=rental)
        if form.is_valid():
            rental = form.save(commit=False)
            # Mantener tarifa desde el vehículo, recalcular días y total
            rental.daily_rate = rental.vehicle.daily_rate
            try:
                if rental.start_date and rental.end_date:
                    delta = rental.end_date - rental.start_date
                    rental.days = delta.days + 1
                    rental.total_amount = rental.days * rental.daily_rate
            except Exception:
                pass

            try:
                rental.full_clean()
                rental.save()
                messages.success(request, 'Reserva actualizada exitosamente.')
                return redirect('my_rentals')
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
    else:
        form = RentalUpdateForm(instance=rental)

    context = {
        'form': form,
        'vehicle': rental.vehicle,
        'rental': rental,
    }
    return render(request, 'rental/rental_edit.html', context)


@login_required
def rental_cancel_user(request, pk):
    """Cancelar una reserva propia"""
    rental = get_object_or_404(Rental, pk=pk, client=request.user)

    if request.method == 'POST':
        if rental.status in ['completado', 'cancelado']:
            messages.warning(request, 'Esta reserva ya no puede cancelarse.')
        else:
            rental.status = 'cancelado'
            rental.save()
            # Liberar vehículo
            rental.vehicle.status = 'disponible'
            rental.vehicle.save()
            messages.success(request, 'Reserva cancelada exitosamente.')
        return redirect('my_rentals')

    return redirect('my_rentals')


# VISTAS DE ADMINISTRACIÓN

def admin_required(view_func):
    """Decorador para requerir rol admin u operador"""
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role not in ['admin', 'operador']:
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


@admin_required
def dashboard(request):
    """Panel de administración"""
    # Estadísticas
    total_vehicles = Vehicle.objects.count()
    available_vehicles = Vehicle.objects.filter(status='disponible').count()
    active_rentals = Rental.objects.filter(status='activo').count()
    total_revenue = Rental.objects.filter(status='completado').aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # Vehículos más alquilados
    top_vehicles = Vehicle.objects.annotate(
        rental_count=Count('rentals')
    ).order_by('-rental_count')[:5]

    # Ingresos por mes (últimos 6 meses) compatible con PostgreSQL/SQLite
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_qs = (
        Rental.objects.filter(status='completado', created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )
    monthly_revenue = [
        {'month': item['month'].strftime('%Y-%m'), 'total': float(item['total'] or 0)}
        for item in monthly_qs
    ]

    # Alquileres recientes
    recent_rentals = Rental.objects.all()[:10]

    # Distribución por estado
    status_distribution = Rental.objects.values('status').annotate(
        count=Count('id')
    )

    context = {
        'total_vehicles': total_vehicles,
        'available_vehicles': available_vehicles,
        'active_rentals': active_rentals,
        'total_revenue': total_revenue,
        'top_vehicles': top_vehicles,
        'monthly_revenue': list(monthly_revenue),
        'recent_rentals': recent_rentals,
        'status_distribution': list(status_distribution),
    }
    return render(request, 'rental/dashboard.html', context)


@admin_required
def vehicles_manage(request):
    """Gestión de vehículos"""
    vehicles = Vehicle.objects.all().select_related('category')
    
    # Filtros
    search = request.GET.get('search')
    if search:
        vehicles = vehicles.filter(
            Q(brand__icontains=search) | 
            Q(model__icontains=search) |
            Q(license_plate__icontains=search)
        )
    
    context = {'vehicles': vehicles}
    return render(request, 'rental/vehicles_manage.html', context)


@admin_required
def vehicle_create(request):
    """Crear vehículo"""
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo creado exitosamente.')
            return redirect('vehicles_manage')
    else:
        form = VehicleForm()
    
    return render(request, 'rental/vehicle_form.html', {'form': form, 'title': 'Crear Vehículo'})


@admin_required
def vehicle_edit(request, pk):
    """Editar vehículo"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo actualizado exitosamente.')
            return redirect('vehicles_manage')
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'rental/vehicle_form.html', {'form': form, 'title': 'Editar Vehículo'})


@admin_required
def vehicle_delete(request, pk):
    """Eliminar vehículo"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehículo eliminado exitosamente.')
        return redirect('vehicles_manage')
    
    return render(request, 'rental/vehicle_confirm_delete.html', {'vehicle': vehicle})


@admin_required
def categories_manage(request):
    """Gestión de categorías"""
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'rental/categories_manage.html', context)


@admin_required
def category_create(request):
    """Crear categoría"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('categories_manage')
    else:
        form = CategoryForm()
    
    return render(request, 'rental/category_form.html', {'form': form, 'title': 'Crear Categoría'})


@admin_required
def category_edit(request, pk):
    """Editar categoría"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('categories_manage')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'rental/category_form.html', {'form': form, 'title': 'Editar Categoría'})


@admin_required
def category_delete(request, pk):
    """Eliminar categoría"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('categories_manage')
    
    return render(request, 'rental/category_confirm_delete.html', {'category': category})


@admin_required
def rentals_manage(request):
    """Gestión de alquileres"""
    rentals = Rental.objects.all().select_related('client', 'vehicle')
    
    # Filtros
    form = RentalFilterForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if search:
            rentals = rentals.filter(
                Q(client__username__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search) |
                Q(vehicle__license_plate__icontains=search)
            )
        if status:
            rentals = rentals.filter(status=status)
        if start_date:
            rentals = rentals.filter(start_date__gte=start_date)
        if end_date:
            rentals = rentals.filter(end_date__lte=end_date)
    
    context = {
        'rentals': rentals,
        'filter_form': form,
    }
    return render(request, 'rental/rentals_manage.html', context)


@admin_required
def rental_update_status(request, pk):
    """Actualizar estado de alquiler"""
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Rental.STATUS_CHOICES):
            rental.status = new_status
            rental.save()
            
            # Si se completa o cancela, liberar el vehículo
            if new_status in ['completado', 'cancelado']:
                rental.vehicle.status = 'disponible'
                rental.vehicle.save()
            
            messages.success(request, 'Estado actualizado exitosamente.')
        
        return redirect('rentals_manage')
    
    return redirect('rentals_manage')


@admin_required
def export_rentals_csv(request):
    """Exportar alquileres a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alquileres.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Cliente', 'Vehículo', 'Fecha Inicio', 'Fecha Fin', 'Días', 'Monto Total', 'Estado'])
    
    rentals = Rental.objects.all().select_related('client', 'vehicle')
    for rental in rentals:
        writer.writerow([
            rental.id,
            rental.client.get_full_name(),
            str(rental.vehicle),
            rental.start_date,
            rental.end_date,
            rental.days,
            rental.total_amount,
            rental.get_status_display(),
        ])
    
    return response


@admin_required
def export_rentals_excel(request):
    """Exportar alquileres a Excel (.xlsx)"""
    # Importación perezosa y manejo de ausencia de paquete
    try:
        from openpyxl import Workbook as _Workbook
    except Exception:
        messages.error(request, 'La exportación a Excel requiere instalar "openpyxl".')
        return redirect('rentals_manage')

    wb = _Workbook()
    ws = wb.active
    ws.title = "Alquileres"
    headers = ['ID', 'Cliente', 'Vehículo', 'Fecha Inicio', 'Fecha Fin', 'Días', 'Monto Total', 'Estado']
    ws.append(headers)

    rentals = Rental.objects.all().select_related('client', 'vehicle')
    for r in rentals:
        ws.append([
            r.id,
            r.client.get_full_name(),
            str(r.vehicle),
            r.start_date.strftime('%Y-%m-%d'),
            r.end_date.strftime('%Y-%m-%d'),
            r.days,
            float(r.total_amount),
            r.get_status_display(),
        ])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    response = HttpResponse(
        bio.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="alquileres.xlsx"'
    return response


@admin_required
def rental_contract_pdf(request, pk):
    """Generar contrato en PDF y descargar"""
    rental = get_object_or_404(Rental, pk=pk)

    # Importación perezosa y manejo de ausencia de paquete
    try:
        from xhtml2pdf import pisa as _pisa
    except Exception:
        messages.error(request, 'La generación de PDF requiere instalar "xhtml2pdf".')
        return redirect('rentals_manage')

    # Resolver rutas de STATIC/MEDIA a filesystem para que xhtml2pdf pueda leer imágenes
    def link_callback(uri, rel):
        # Mapear STATIC
        if uri.startswith(settings.STATIC_URL):
            path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ''))
            return path if os.path.exists(path) else uri
        # Mapear MEDIA
        if uri.startswith(settings.MEDIA_URL):
            path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))
            return path if os.path.exists(path) else uri
        # Devolver URI tal cual para URLs absolutas (http/https)
        return uri

    html = render_to_string('rental/rental_contract.html', {'rental': rental})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contrato_{rental.id}.pdf"'
    _pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    return response
