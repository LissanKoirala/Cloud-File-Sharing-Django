from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from . models import Device
from django.contrib.auth.decorators import login_required
from users.models import Profile
import socket

@login_required(login_url='/info')
def home(request):
    if request.GET:
        device = request.GET['device']
        try:
            device = socket.gethostbyname(device)
            return HttpResponseRedirect(f"http://{device}:8000")
        except:
            return render(request, 'not-active.html', {'device':device})
 
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = Profile(user=request.user)
        profile.save()
        profile = Profile.objects.get(user=request.user)

    status = profile.account_activated

    if status == False:
        return redirect('activate')


    devices = Device.objects.filter(user=request.user).order_by('-date_device_added')
    context = {'devices':devices}
    return render(request, 'home.html', context)

@login_required
def add_device(request):

    if request.GET:
        hostname = request.GET['hostname']

        user_devices = Device(user=request.user, hostname=hostname)
        user_devices.save()

        return redirect('home')



    return render(request, 'add-device.html')



def help_page(request):
    return render(request, 'help.html', {'who_user':request.user})


def view_404(request, exception):
    return render(request, '404.html')
