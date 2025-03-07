# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Symptom, Medication, Prescription, Staff, Invoice, FinancialRecord, Supply, LoginTicket, UserProfile
from .forms import PrescriptionForm, MedicationForm, StaffForm, FinancialRecordForm, SupplyForm, RegistrationForm

def register(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    """Handle user login and track login ticket"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Track login ticket
            ip_address = request.META.get('REMOTE_ADDR')
            LoginTicket.objects.create(user=user, ip_address=ip_address)
            messages.success(request, 'Login successful!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

@login_required
def user_logout(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'Logout successful!')
    return redirect('login')

@login_required
def home(request):
    """Render the main dashboard based on user role"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.role == 'ADMIN':  # Admin/Manager view
            staff_count = Staff.objects.count()
            total_revenue = FinancialRecord.objects.filter(transaction_type='INCOME').aggregate(models.Sum('amount'))['amount__sum'] or 0
            total_expenses = FinancialRecord.objects.filter(transaction_type='EXPENSE').aggregate(models.Sum('amount'))['amount__sum'] or 0
            return render(request, 'admin_dashboard.html', {
                'staff_count': staff_count,
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
            })
        else:  # Doctor view
            medications = Medication.objects.all()[:5]
            return render(request, 'doctor_dashboard.html', {
                'medications': medications
            })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('login')
    except Exception as e:
        messages.error(request, 'An unexpected error occurred.')
        return render(request, 'doctor_dashboard.html')

# Prescription Generation
@login_required
def create_prescription(request):
    """Generate a new prescription"""
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role != 'DOCTOR':
        messages.error(request, 'Only doctors can create prescriptions.')
        return redirect('home')
    try:
        if request.method == 'POST':
            form = PrescriptionForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    prescription = form.save()
                    # Generate invoice
                    total_amount = sum(med.price for med in prescription.medications.all())
                    Invoice.objects.create(prescription=prescription, total_amount=total_amount)
                    # Update financial record
                    FinancialRecord.objects.create(
                        description=f"Prescription for {prescription.patient_name}",
                        amount=total_amount,
                        transaction_type='INCOME'
                    )
                messages.success(request, 'Prescription generated successfully!')
                return redirect('prescription_detail', pk=prescription.pk)
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = PrescriptionForm()
        return render(request, 'prescription_form.html', {'form': form})
    except Exception as e:
        messages.error(request, 'Error generating prescription.')
        return render(request, 'prescription_form.html', {'form': form})

@login_required
def prescription_detail(request, pk):
    """Display prescription details"""
    try:
        prescription = Prescription.objects.select_related().get(pk=pk)
        invoice = Invoice.objects.filter(prescription=prescription).first()
        return render(request, 'prescription_detail.html', {
            'prescription': prescription,
            'invoice': invoice
        })
    except Prescription.DoesNotExist:
        messages.error(request, 'Prescription not found.')
        return redirect('home')

# Medication (Inventory) Management - Doctor
@login_required
def manage_medications(request):
    """Manage medications (inventory)"""
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role != 'DOCTOR':
        messages.error(request, 'Only doctors can manage medications.')
        return redirect('home')
    try:
        medications = Medication.objects.all()
        if request.method == 'POST':
            form = MedicationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Medication added successfully!')
                return redirect('manage_medications')
        else:
            form = MedicationForm()
        return render(request, 'manage_medications.html', {
            'medications': medications,
            'form': form
        })
    except Exception as e:
        messages.error(request, 'Error managing medications.')
        return render(request, 'manage_medications.html')

# Staff Management - Admin/Manager
@login_required
def manage_staff(request):
    """Manage staff members"""
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role != 'ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    try:
        staff = Staff.objects.all()
        if request.method == 'POST':
            form = StaffForm(request.POST)
            if form.is_valid():
                form.save()
                # Add to financial record for salary expense
                staff_member = form.instance
                FinancialRecord.objects.create(
                    description=f"Salary for {staff_member.name}",
                    amount=staff_member.salary,
                    transaction_type='EXPENSE'
                )
                messages.success(request, 'Staff member added successfully!')
                return redirect('manage_staff')
        else:
            form = StaffForm()
        return render(request, 'manage_staff.html', {
            'staff': staff,
            'form': form
        })
    except Exception as e:
        messages.error(request, 'Error managing staff.')
        return render(request, 'manage_staff.html')

# Financial Management - Admin/Manager
@login_required
def manage_finances(request):
    """Manage financial records"""
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role != 'ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    try:
        records = FinancialRecord.objects.all().order_by('-created_at')
        if request.method == 'POST':
            form = FinancialRecordForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Financial record added successfully!')
                return redirect('manage_finances')
        else:
            form = FinancialRecordForm()
        return render(request, 'manage_finances.html', {
            'records': records,
            'form': form
        })
    except Exception as e:
        messages.error(request, 'Error managing finances.')
        return render(request, 'manage_finances.html')

# Supply (Goods) Management - Admin/Manager
@login_required
def manage_supplies(request):
    """Manage supplies"""
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role != 'ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    try:
        supplies = Supply.objects.all()
        if request.method == 'POST':
            form = SupplyForm(request.POST)
            if form.is_valid():
                form.save()
                # Add to financial record for expense
                supply = form.instance
                FinancialRecord.objects.create(
                    description=f"Purchase of {supply.name}",
                    amount=supply.price_per_unit * supply.quantity,
                    transaction_type='EXPENSE'
                )
                messages.success(request, 'Supply added successfully!')
                return redirect('manage_supplies')
        else:
            form = SupplyForm()
        return render(request, 'manage_supplies.html', {
            'supplies': supplies,
            'form': form
        })
    except Exception as e:
        messages.error(request, 'Error managing supplies.')
        return render(request, 'manage_supplies.html')

# Login Ticket Tracking - Admin/Manager
@login_required
def manage_login_tickets(request):
    """View login tickets"""
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role != 'ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    try:
        tickets = LoginTicket.objects.all().order_by('-login_time')
        return render(request, 'manage_login_tickets.html', {
            'tickets': tickets
        })
    except Exception as e:
        messages.error(request, 'Error viewing login tickets.')
        return render(request, 'manage_login_tickets.html')