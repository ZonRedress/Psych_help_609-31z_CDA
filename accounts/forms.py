from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
import re

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone') 
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Иван'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Иванов'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@mail.ru'}),
            'phone': forms.TextInput(attrs={'placeholder': '+79001234567'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Делаем ВСЕ поля обязательными
        for field in self.fields.values():
            field.required = True
            field.widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # АВТОГЕНЕРАЦИЯ ЛОГИНА
        email = self.cleaned_data.get('email')
        base_username = email.split('@')[0] 
        
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username)
        if not base_username:
            base_username = 'user'
            
        username = base_username
        counter = 1
        
        # Проверяем на уникальность
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        user.username = username
        
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'you@mail.ru'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password) and user.is_active:
                    self.user_cache = user
                else:
                    raise self.get_invalid_login_error()
            except User.DoesNotExist:
                raise self.get_invalid_login_error()
        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'photo')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # В профиле тоже делаем все текстовые поля обязательными (кроме фото)
        for field_name, field in self.fields.items():
            if field_name != 'photo':
                field.required = True


class PsychologistProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'photo', 'experience_years', 'bio')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'photo':
                field.required = True