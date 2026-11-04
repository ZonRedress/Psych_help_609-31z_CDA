from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils import timezone

from accounts.models import User
from accounts.forms import PsychologistProfileForm
from .forms import DirectAppointmentForm, ScheduleForm, AppointmentEditForm
from .models import Schedule, Appointment

# ---------- Публичные страницы ----------

class HomeView(ListView):
    model = User
    template_name = 'home.html'
    context_object_name = 'psychologists'

    def get_queryset(self):
        Appointment.update_overdue_statuses() 
        return User.objects.filter(role=User.ROLE_PSYCHOLOGIST)


class ScheduleListView(ListView):
    model = Schedule
    template_name = 'booking/schedule.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        return Schedule.objects.filter(
            status=Schedule.STATUS_FREE,
            datetime_from__gte=timezone.now()
        ).select_related('psychologist').order_by('datetime_from')

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_client():
            messages.error(request, 'Только клиенты могут записываться.')
            return redirect('login')

        schedule_id = request.POST.get('schedule_id')
        schedule = get_object_or_404(Schedule, pk=schedule_id, status=Schedule.STATUS_FREE)

        Appointment.objects.create(
            client=request.user,
            schedule=schedule,
            topic="Первая консультация",
            notes="",
            status=Appointment.STATUS_PLANNED
        )
        
        schedule.status = Schedule.STATUS_BOOKED
        schedule.save(update_fields=['status'])

        messages.success(request, 'Вы успешно записались на консультацию!')
        return redirect('client_dashboard')


class PsychologistDetailView(DetailView):
    model = User
    template_name = 'booking/psychologist_detail.html'
    context_object_name = 'psychologist'

    def get_queryset(self):
        return User.objects.filter(role=User.ROLE_PSYCHOLOGIST)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['free_slots'] = Schedule.objects.filter(
            psychologist=self.object,
            status=Schedule.STATUS_FREE,
            datetime_from__gte=timezone.now()
        )
        return ctx

    def post(self, request, *args, **kwargs):
        # Обработка формы записи прямо на странице психолога
        if not request.user.is_authenticated or not request.user.is_client():
            messages.error(request, 'Только клиенты могут записываться.')
            return redirect('login')

        schedule_id = request.POST.get('schedule_id')
        schedule = get_object_or_404(Schedule, pk=schedule_id, status=Schedule.STATUS_FREE)

        Appointment.objects.create(
            client=request.user,
            schedule=schedule,
            topic="Первая консультация",
            notes="",
            status=Appointment.STATUS_PLANNED
        )
        
        schedule.status = Schedule.STATUS_BOOKED
        schedule.save(update_fields=['status'])

        messages.success(request, 'Вы успешно записались на консультацию!')
        return redirect('client_dashboard')

# ---------- Клиент ----------

class ClientDashboardView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'booking/client_dashboard.html'
    context_object_name = 'appointments'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_client():
            messages.error(request, 'Страница доступна только клиентам.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        Appointment.update_overdue_statuses()
        return Appointment.objects.filter(client=self.request.user).select_related('schedule', 'schedule__psychologist').order_by('-schedule__datetime_from')


class CancelAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        
        if request.user.is_client() and appointment.client != request.user:
            messages.error(request, 'Вы не можете удалить чужую запись.')
            return redirect('client_dashboard')
            
        if request.user.is_psychologist() and appointment.schedule.psychologist != request.user:
            messages.error(request, 'Вы не можете удалить чужую запись.')
            return redirect('psychologist_dashboard')

        schedule = appointment.schedule
        appointment.delete()
        
        if request.user.is_psychologist():
            schedule.delete()
        else:
            schedule.status = Schedule.STATUS_FREE
            schedule.save(update_fields=['status'])
        
        messages.success(request, 'Запись отменена.')
        if request.user.is_psychologist():
            return redirect('psychologist_dashboard')
        return redirect('client_dashboard')


# ---------- Психолог ----------

class PsychologistRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_psychologist():
            messages.error(request, 'Страница доступна только психологам.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class PsychologistDashboardView(PsychologistRequiredMixin, ListView):
    model = Schedule
    template_name = 'booking/psychologist_dashboard.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        Appointment.update_overdue_statuses()
        return Schedule.objects.filter(psychologist=self.request.user, status=Schedule.STATUS_FREE).order_by('datetime_from')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['appointments'] = Appointment.objects.filter(
            schedule__psychologist=self.request.user
        ).select_related('client', 'schedule').order_by('-schedule__datetime_from')
        
        ctx['profile_form'] = PsychologistProfileForm(instance=self.request.user)
        ctx['direct_form'] = DirectAppointmentForm()
        ctx['schedule_form'] = ScheduleForm(psychologist=self.request.user)
        return ctx

    def post(self, request, *args, **kwargs):
        if 'update_profile' in request.POST:
            form = PsychologistProfileForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Профиль обновлен!')
            else:
                messages.error(request, 'Ошибка обновления профиля.')
            return redirect('psychologist_dashboard')
        
        elif 'add_consultation' in request.POST:
            form = DirectAppointmentForm(request.POST)
            if form.is_valid():
                form.save(psychologist=request.user)
                messages.success(request, 'Запись успешно создана!')
            else:
                messages.error(request, 'Ошибка создания записи.')
            return redirect('psychologist_dashboard')
            
        elif 'add_slot' in request.POST:
            form = ScheduleForm(request.POST, psychologist=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Свободное окно добавлено!')
            else:
                messages.error(request, 'Ошибка создания окна (возможно, пересекается с другим).')
            return redirect('psychologist_dashboard')

        return super().post(request, *args, **kwargs)


class AppointmentUpdateView(PsychologistRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentEditForm
    template_name = 'booking/appointment_edit.html'
    success_url = reverse_lazy('psychologist_dashboard')

    def get_queryset(self):
        return Appointment.objects.filter(schedule__psychologist=self.request.user)


class DeleteScheduleView(PsychologistRequiredMixin, View):
    def post(self, request, pk):
        schedule = get_object_or_404(Schedule, pk=pk, psychologist=request.user)
        if schedule.status == Schedule.STATUS_FREE:
            schedule.delete()
            messages.success(request, 'Свободное окно удалено.')
        else:
            messages.error(request, 'Нельзя удалить занятое окно.')
        return redirect('psychologist_dashboard')