from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CLIENT = 'client'
    ROLE_PSYCHOLOGIST = 'psychologist'
    ROLE_CHOICES = (
        (ROLE_CLIENT, 'Клиент'),
        (ROLE_PSYCHOLOGIST, 'Психолог'),
    )

    email = models.EmailField('Email', unique=True)
    
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    phone = models.CharField('Телефон', max_length=20, blank=True, null=True)
    photo = models.ImageField('Фото', upload_to='photos/', blank=True, null=True)
    
    experience_years = models.PositiveIntegerField('Опыт работы (лет)', default=0, blank=True)
    bio = models.TextField('О себе (специализация)', max_length=1000, blank=True)

    def is_client(self):
        return self.role == self.ROLE_CLIENT

    def is_psychologist(self):
        return self.role == self.ROLE_PSYCHOLOGIST

    def __str__(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username