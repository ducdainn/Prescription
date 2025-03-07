# forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Prescription, Medication, Staff, FinancialRecord, Supply, UserProfile

class RegistrationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Admin/Manager'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient_name', 'symptoms', 'medications', 'notes']
        widgets = {
            'symptoms': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'medications': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        symptoms = cleaned_data.get('symptoms')
        medications = cleaned_data.get('medications')
        if not symptoms:
            raise forms.ValidationError("At least one symptom must be selected.")
        if not medications:
            raise forms.ValidationError("At least one medication must be selected.")
        return cleaned_data

class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ['name', 'dosage_instructions', 'common_side_effects', 'quantity_in_stock', 'price']
        widgets = {
            'dosage_instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'common_side_effects': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'role', 'salary']

class FinancialRecordForm(forms.ModelForm):
    class Meta:
        model = FinancialRecord
        fields = ['description', 'amount', 'transaction_type']

class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ['name', 'quantity', 'price_per_unit']