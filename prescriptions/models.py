# models.py
from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django.contrib.auth.models import User

# User Profile to distinguish between Doctor and Admin/Manager
class UserProfile(models.Model):
    USER_ROLES = (
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Admin/Manager'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=USER_ROLES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Symptom for prescription generation
class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

# Medication (Inventory) - Used by Doctor
class Medication(models.Model):
    name = models.CharField(max_length=100, unique=True)
    dosage_instructions = models.TextField()
    common_side_effects = models.TextField(blank=True)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.name

# Prescription - Links symptoms and medications
class Prescription(models.Model):
    patient_name = models.CharField(max_length=200, validators=[MinLengthValidator(2)])
    symptoms = models.ManyToManyField(Symptom)
    medications = models.ManyToManyField(Medication)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription for {self.patient_name}"

# Staff - Managed by Admin/Manager
class Staff(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

# Invoice - Generated for prescriptions
class Invoice(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice for {self.prescription.patient_name}"

# Financial Record - For managing finances
class FinancialRecord(models.Model):
    TRANSACTION_TYPES = (
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.description}"

# Goods/Supplies - Separate from medications
class Supply(models.Model):
    name = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField(default=0)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

# Login Ticket - Track user logins
class LoginTicket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f"Login by {self.user.username} at {self.login_time}"