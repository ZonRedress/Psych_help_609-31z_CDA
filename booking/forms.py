from django import forms
from accounts.models import User
from .models import Schedule, Appointment
from django.utils import timezone
import datetime


class DirectAppointmentForm(forms.Form):
    """Форма для психолога: создание записи сразу для клиента"""
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.ROLE_CLIENT, is_staff=False, is_superuser=False),
        label="Клиент",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(label="Дата начала", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time_from = forms.TimeField(label="Время начала", widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    date_to = forms.DateField(label="Дата окончания", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time_to = forms.TimeField(label="Время окончания", widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    
    topic = forms.CharField(label="Тема консультации", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Тревожность'}))
    notes = forms.CharField(label="Дополнительные заметки", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Что нужно обсудить?'}))

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        time_from = cleaned_data.get('time_from')
        date_to = cleaned_data.get('date_to')
        time_to = cleaned_data.get('time_to')

        if date_from and time_from and date_to and time_to:
            dt_from = datetime.datetime.combine(date_from, time_from)
            dt_to = datetime.datetime.combine(date_to, time_to)

            if dt_from >= dt_to:
                raise forms.ValidationError('Время окончания должно быть позже времени начала.')
                
            self.dt_from_combined = dt_from
            self.dt_to_combined = dt_to
        return cleaned_data

    def save(self, psychologist):
        schedule = Schedule.objects.create(
            psychologist=psychologist,
            datetime_from=self.dt_from_combined,
            datetime_to=self.dt_to_combined,
            status=Schedule.STATUS_BOOKED
        )
        return Appointment.objects.create(
            client=self.cleaned_data['client'],
            schedule=schedule,
            topic=self.cleaned_data['topic'],
            notes=self.cleaned_data['notes'],
            status=Appointment.STATUS_PLANNED
        )


class ScheduleForm(forms.Form):
    """Форма для создания СВОБОДНЫХ окон"""
    date_from = forms.DateField(label="Дата", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time_from = forms.TimeField(label="Начало", widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    time_to = forms.TimeField(label="Конец", widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

    def __init__(self, *args, psychologist=None, **kwargs):
        self.psychologist = psychologist
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        time_from = cleaned_data.get('time_from')
        time_to = cleaned_data.get('time_to')

        if date_from and time_from and time_to:
            dt_from = datetime.datetime.combine(date_from, time_from)
            dt_to = datetime.datetime.combine(date_from, time_to)

            if dt_from >= dt_to:
                raise forms.ValidationError('Время окончания должно быть позже времени начала.')
            
            if self.psychologist:
                overlaps = Schedule.objects.filter(
                    psychologist=self.psychologist,
                    datetime_from__lt=dt_to,
                    datetime_to__gt=dt_from
                )
                if overlaps.exists():
                    raise forms.ValidationError('Этот слот пересекается с существующим.')
                
            self.dt_from_combined = dt_from
            self.dt_to_combined = dt_to
        return cleaned_data

    def save(self):
        return Schedule.objects.create(
            psychologist=self.psychologist,
            datetime_from=self.dt_from_combined,
            datetime_to=self.dt_to_combined,
            status=Schedule.STATUS_FREE
        )


class BookAppointmentForm(forms.ModelForm):
    """Форма для КЛИЕНТА: запись на свободное окно"""
    class Meta:
        model = Appointment
        fields = ('topic', 'notes')
        widgets = {
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Тревожность'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Что бы вы хотели обсудить?'}),
        }


class AppointmentEditForm(forms.ModelForm):
    """Форма для редактирования существующей записи"""
    date_from = forms.DateField(label="Дата начала", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time_from = forms.TimeField(label="Время начала", widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    date_to = forms.DateField(label="Дата окончания", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time_to = forms.TimeField(label="Время окончания", widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

    class Meta:
        model = Appointment
        fields = ('client', 'topic', 'notes', 'status')
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'topic': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = User.objects.filter(role=User.ROLE_CLIENT, is_staff=False, is_superuser=False)
        
        if self.instance and self.instance.pk:
            dt_from = timezone.localtime(self.instance.schedule.datetime_from)
            dt_to = timezone.localtime(self.instance.schedule.datetime_to)
            self.fields['date_from'].initial = dt_from.date()
            self.fields['time_from'].initial = dt_from.time()
            self.fields['date_to'].initial = dt_to.date()
            self.fields['time_to'].initial = dt_to.time()

    def save(self, commit=True):
        appointment = super().save(commit=False)
        if commit:
            appointment.save()
            schedule = appointment.schedule
            schedule.datetime_from = datetime.datetime.combine(self.cleaned_data['date_from'], self.cleaned_data['time_from'])
            schedule.datetime_to = datetime.datetime.combine(self.cleaned_data['date_to'], self.cleaned_data['time_to'])
            schedule.save()
        return appointment