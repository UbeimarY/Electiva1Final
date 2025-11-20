from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Vehicle, Category, Rental, UserProfile


class UserRegistrationForm(UserCreationForm):
    """Formulario de registro de usuarios"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, max_length=30)
    last_name = forms.CharField(required=True, max_length=30)
    phone = forms.CharField(required=False, max_length=20)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
    identification = forms.CharField(required=False, max_length=50)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Crear perfil de usuario
            UserProfile.objects.create(
                user=user,
                role='cliente',
                phone=self.cleaned_data.get('phone', ''),
                address=self.cleaned_data.get('address', ''),
                identification=self.cleaned_data.get('identification', '')
            )
        
        return user


class VehicleForm(forms.ModelForm):
    """Formulario para vehículos"""
    class Meta:
        model = Vehicle
        fields = ['license_plate', 'brand', 'model', 'year', 'category', 'transmission', 
                  'daily_rate', 'capacity', 'status', 'image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_license_plate(self):
        license_plate = self.cleaned_data.get('license_plate')
        if license_plate:
            # Verificar duplicados (excluyendo la instancia actual si es edición)
            qs = Vehicle.objects.filter(license_plate=license_plate)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Ya existe un vehículo con esta placa.')
        return license_plate


class CategoryForm(forms.ModelForm):
    """Formulario para categorías"""
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            qs = Category.objects.filter(name=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Ya existe una categoría con este nombre.')
        return name


class RentalForm(forms.ModelForm):
    """Formulario para alquileres"""
    class Meta:
        model = Rental
        fields = ['vehicle', 'start_date', 'end_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar vehículos disponibles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(status='disponible')


class RentalUpdateForm(forms.ModelForm):
    """Formulario para edición de alquileres por el cliente"""
    class Meta:
        model = Rental
        fields = ['start_date', 'end_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class RentalFilterForm(forms.Form):
    """Formulario para filtros de búsqueda"""
    search = forms.CharField(required=False, label='Buscar')
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Rental.STATUS_CHOICES,
        label='Estado'
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Desde'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Hasta'
    )
