from django.contrib import admin
from django.utils import timezone
from .models import Schedule, Appointment


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'psychologist', 'datetime_from', 'datetime_to', 'status')
    list_filter = ('status', 'psychologist')
    search_fields = ('psychologist__username', 'psychologist__last_name')
    date_hierarchy = 'datetime_from'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'get_start_time', 'get_end_time', 'status', 'topic')
    list_filter = ('status',)
    search_fields = ('client__username', 'client__last_name', 'topic')

    @admin.display(description='Начало')
    def get_start_time(self, obj):
        return timezone.localtime(obj.schedule.datetime_from).strftime('%d.%m.%Y %H:%M')

    @admin.display(description='Конец')
    def get_end_time(self, obj):
        return timezone.localtime(obj.schedule.datetime_to).strftime('%d.%m.%Y %H:%M')