# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .twilio_service.py import TwilioService

twilio_service = TwilioService()

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                request.session['pre_mfa_user_id'] = user.id
                # Assuming user has a profile with a phone_number field
                phone_number = user.profile.phone_number
                twilio_service.send_verification_code(phone_number)
                return redirect('mfa_verification')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
    
    form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def mfa_verification_view(request):
    if request.method == "POST":
        code = request.POST.get('code')
        user_id = request.session.get('pre_mfa_user_id')
        if not user_id:
            return redirect('login')
        
        user = get_user_model().objects.get(id=user_id)
        phone_number = user.profile.phone_number
        verification_check = twilio_service.check_verification_code(phone_number, code)
        if verification_check.status == 'approved':
            login(request, user)
            del request.session['pre_mfa_user_id']
            return redirect('home')
        else:
            messages.error(request, "Invalid verification code. Please try again.")
    
    return render(request, 'accounts/mfa_verification.html')