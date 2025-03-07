# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('prescription/create/', views.create_prescription, name='create_prescription'),
    path('prescription/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('medications/', views.manage_medications, name='manage_medications'),
    path('staff/', views.manage_staff, name='manage_staff'),
    path('finances/', views.manage_finances, name='manage_finances'),
    path('supplies/', views.manage_supplies, name='manage_supplies'),
    path('login-tickets/', views.manage_login_tickets, name='manage_login_tickets'),
]