from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.ScheduleListView.as_view(), name='schedule_list'),
    path('psychologists/<int:pk>/', views.PsychologistDetailView.as_view(), name='psychologist_detail'),
    path('dashboard/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('appointment/<int:pk>/cancel/', views.CancelAppointmentView.as_view(), name='cancel_appointment'),
    path('psychologist/dashboard/', views.PsychologistDashboardView.as_view(), name='psychologist_dashboard'),
    path('psychologist/appointment/<int:pk>/edit/', views.AppointmentUpdateView.as_view(), name='appointment_edit'),
    path('psychologist/schedule/<int:pk>/delete/', views.DeleteScheduleView.as_view(), name='slot_delete'),
]