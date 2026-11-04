from django.conf import settings
from django.db import models
from django.utils import timezone


class Schedule(models.Model):
    STATUS_FREE = 'free'
    STATUS_BOOKED = 'booked'
    STATUS_CHOICES = (
        (STATUS_FREE, 'Свободен'),
        (STATUS_BOOKED, 'Забронирован'),
    )

    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'role': 'psychologist'},
        verbose_name='Психолог',
    )
    datetime_from = models.DateTimeField('Начало')
    datetime_to = models.DateTimeField('Окончание')
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default=STATUS_FREE)

    class Meta:
        verbose_name = 'Слот расписания'
        verbose_name_plural = 'Расписание'
        ordering = ('datetime_from',)

    def __str__(self):
        # ИСПРАВЛЕНИЕ: Переводим время в локальное (Москву) перед выводом
        local_time = timezone.localtime(self.datetime_from)
        return f'{self.psychologist} — {local_time:%d.%m.%Y %H:%M}'

    def is_past(self):
        return self.datetime_from < timezone.now()


class Appointment(models.Model):
    STATUS_PLANNED = 1
    STATUS_COMPLETED = 2
    STATUS_CHOICES = (
        (STATUS_PLANNED, 'Запланирована'),
        (STATUS_COMPLETED, 'Завершена'),
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        limit_choices_to={'role': 'client'},
        verbose_name='Клиент',
    )
    schedule = models.OneToOneField(
        Schedule,
        on_delete=models.CASCADE,
        related_name='appointment',
        verbose_name='Слот',
    )
    status = models.PositiveSmallIntegerField('Статус', choices=STATUS_CHOICES, default=STATUS_PLANNED)
    topic = models.CharField('Тема консультации', max_length=255, blank=True)
    notes = models.TextField('Заметки', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Консультация'
        verbose_name_plural = 'Консультации'
        ordering = ('-schedule__datetime_from',)

    @classmethod
    def update_overdue_statuses(cls):
        """Автоматически завершает консультации, время которых уже прошло"""
        now = timezone.now()
        cls.objects.filter(
            status=cls.STATUS_PLANNED,
            schedule__datetime_to__lt=now
        ).update(status=cls.STATUS_COMPLETED)

    def __str__(self):
        return f'{self.client} → {self.schedule}'