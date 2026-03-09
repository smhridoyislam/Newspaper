from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import CustomUser, EmailVerificationToken


def register_view(request):
    """Handle user registration with email verification"""
    if request.user.is_authenticated:
        return redirect('articles:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email verified
            user.save()
            
            # Create verification token
            token = EmailVerificationToken.objects.create(user=user)
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'token': token.token})
            )
            
            subject = 'Verify Your Email - Newspaper Site'
            html_message = render_to_string('accounts/email/verification_email.html', {
                'user': user,
                'verification_url': verification_url,
            })
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                messages.success(
                    request, 
                    'Registration successful! Please check your email to verify your account.'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'Account created but email could not be sent. Please contact support. Error: {str(e)}'
                )
            
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def verify_email_view(request, token):
    """Verify user email with token"""
    verification_token = get_object_or_404(EmailVerificationToken, token=token)
    
    if verification_token.is_valid():
        user = verification_token.user
        user.is_active = True
        user.is_email_verified = True
        user.save()
        
        verification_token.is_used = True
        verification_token.save()
        
        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('accounts:register')


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('articles:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if not user.is_email_verified and not user.is_superuser:
                    messages.warning(request, 'Please verify your email before logging in.')
                    return redirect('accounts:login')
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Redirect editors to dashboard
                if user.is_editor():
                    return redirect('articles:editor_dashboard')
                return redirect('articles:home')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('articles:home')


@login_required
def profile_view(request):
    """View and edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})


def resend_verification_view(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email, is_email_verified=False)
            
            # Create new verification token
            token = EmailVerificationToken.objects.create(user=user)
            
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'token': token.token})
            )
            
            subject = 'Verify Your Email - Newspaper Site'
            html_message = render_to_string('accounts/email/verification_email.html', {
                'user': user,
                'verification_url': verification_url,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, 'Verification email sent! Please check your inbox.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No unverified account found with this email.')
        except Exception as e:
            messages.error(request, f'Could not send email: {str(e)}')
    
    return render(request, 'accounts/resend_verification.html')
