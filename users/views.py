from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm
from users.models import Profile
from django.http import HttpResponseRedirect
from django.contrib import messages, auth
from django.contrib.auth.models import User
from django.core.mail import send_mail, get_connection
import os
from fileshare.settings import BASE_DIR


# Sending dynamic emails
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')

            messages.success(request, f'Your account has been created! You are now able to log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

 
@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('home')

    else:
        u_form = UserUpdateForm(instance=request.user)

    context = { 
        'u_form': u_form,
    }

    return render(request, 'users/profile.html', context)

@login_required
def account_activation(request):

    profile = Profile(user=request.user)
    status = profile.account_activated


    if status == True:
        return redirect('home')

    if request.GET:

        user_id = request.GET['id']

        try:
            profile = Profile.objects.get(activation_id=user_id)
        except:
            return render(request, 'account_activation.html', {'error':'Invalid code.'})

        profile.folder_id = user_id[::-1]
        profile.account_activated = True
        profile.save()

        try:
            os.mkdir(str(BASE_DIR) + '/uploads/' + str(user_id[::-1]))
            return render(request, 'account_activation.html', {'success':'Success, Your Account has been activated! You can now start uploading files and recover your passwords if necessary.'})
        except:
            return redirect('home')

    else:
 
        import random

        user = User.objects.get(id=request.user.id)
        user_email = user.email

        appha = 'abcde0fghij1klmnop4q2rst3uvwx5yzABC6DEFGHI7JKLM8NOP9QRS0TUVWXYZ'

        code = ""

        for i in range(26):
            x = random.randint(0, 62)
            code += appha[x]

        profile = Profile.objects.get(user=request.user)
        profile.activation_id = code
        profile.save()

        link = f"https://fileshare.ml/activate?id={code}"

        html_message = render_to_string('accountactivation.html', {'username': request.user, 'link':link})
        plain_message = strip_tags(html_message)

        mail.send_mail('Account Activation - FileShare', plain_message, 'auth.nayasambandha@gmail.com', [user_email], html_message=html_message)

        return render(request, 'account_activation.html', {'email':user_email})


