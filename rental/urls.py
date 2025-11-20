from django.urls import path
from . import views

urlpatterns = [
    # Públicas
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Cliente
    path('vehicles/', views.vehicles_list, name='vehicles_list'),
    path('rental/create/<int:vehicle_id>/', views.rental_create, name='rental_create'),
    path('my-rentals/', views.my_rentals, name='my_rentals'),
    path('my-rentals/edit/<int:pk>/', views.rental_edit_user, name='rental_edit_user'),
    path('my-rentals/cancel/<int:pk>/', views.rental_cancel_user, name='rental_cancel_user'),
    
    # Administración
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Vehículos
    path('dashboard/vehicles/', views.vehicles_manage, name='vehicles_manage'),
    path('dashboard/vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('dashboard/vehicles/edit/<int:pk>/', views.vehicle_edit, name='vehicle_edit'),
    path('dashboard/vehicles/delete/<int:pk>/', views.vehicle_delete, name='vehicle_delete'),
    
    # Categorías
    path('dashboard/categories/', views.categories_manage, name='categories_manage'),
    path('dashboard/categories/create/', views.category_create, name='category_create'),
    path('dashboard/categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('dashboard/categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    
    # Alquileres
    path('dashboard/rentals/', views.rentals_manage, name='rentals_manage'),
    path('dashboard/rentals/status/<int:pk>/', views.rental_update_status, name='rental_update_status'),
    path('dashboard/rentals/export/', views.export_rentals_csv, name='export_rentals_csv'),
    path('dashboard/rentals/contract/<int:pk>/', views.rental_contract_pdf, name='rental_contract_pdf'),
    path('dashboard/rentals/export/xlsx/', views.export_rentals_excel, name='export_rentals_excel'),
]
