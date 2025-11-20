from django.contrib import admin
from .models import Category, Vehicle, UserProfile, Rental


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['license_plate', 'brand', 'model', 'year', 'category', 'status', 'daily_rate']
    list_filter = ['status', 'category', 'transmission']
    search_fields = ['license_plate', 'brand', 'model']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'vehicle', 'start_date', 'end_date', 'days', 'total_amount', 'status']
    list_filter = ['status', 'start_date']
    search_fields = ['client__username', 'vehicle__license_plate']
    date_hierarchy = 'start_date'
