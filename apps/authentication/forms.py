# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from apps.home.models import UserProfile


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "First Name",
                "class": "form-control"
            }
        ), required=True)
    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last Name",
                "class": "form-control"
            }
        ), required=True)
    phone_number = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Phone Number",
                "class": "form-control"
            }
        ), required=True)
    ic_number = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "IC Number",
                "class": "form-control"
            }
        ), required=True)
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control"
            }
        ))
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password check",
                "class": "form-control"
            }
        ))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number', 'ic_number')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(user=user, phone_number=self.cleaned_data['phone_number'], ic_number=self.cleaned_data['ic_number'])
        return user
    
class MFAEnableForm(forms.Form):
    pass  # No fields needed for enabling MFA

class MFAVerifyForm(forms.Form):
    token = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': 'Enter MFA token'}))