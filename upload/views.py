from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
import os
import glob
from users.models import Profile
from devices.models import Device
import shutil
from fileshare.settings import BASE_DIR
from django.contrib.auth.decorators import login_required

from .models import File
import random

from django.core.mail import send_mail, EmailMessage

# Sending dynamic emails
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

BASE_DIR = str(BASE_DIR)

def get_directory_size(directory):
    """Returns the `directory` size in bytes."""
    total = 0
    try:
        # print("[+] Getting the size of", directory)
        for entry in os.scandir(directory):
            if entry.is_file():
                # if it's a file, use stat() function
                total += entry.stat().st_size
            elif entry.is_dir():
                # if it's a directory, recursively call this function
                total += get_directory_size(entry.path)
    except NotADirectoryError:
        # if `directory` isn't a directory, get the file size then
        return os.path.getsize(directory)
    except PermissionError:
        # if for whatever reason we can't open the folder, return 0
        return 0
    return total

def get_size_format(b, factor=1024, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


@login_required
def dashboard(request):

    # Checking if the user has activated email or not
    # -----------------------------------------------
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = Profile(user=request.user)
        profile.save()
        profile = Profile.objects.get(user=request.user)

    status = profile.account_activated

    if status == False:
        return redirect('activate')
    # -----------------------------------------------


    # Showing the recent files
    # ------------------------
    profile = Profile.objects.filter(user=request.user).first()
    folder_id = str(profile.folder_id)

    all_files = File.objects.filter(user=request.user).order_by('-data_last_modified').filter(in_bin = False)

    # Total numbers of file
    total_files = len(next(os.walk(str(BASE_DIR) + '/uploads/' + folder_id + '/'))[2]) 

    show_file = all_files[:3]

    size = get_size_format(get_directory_size(str(BASE_DIR) + '/uploads/' + folder_id + '/'))

    # ------------------------------------------------------------------------- #

    # Getting the redirect if it is set, maily used for dashboard as adter uploading files
    # Users will be redirected to the same page


    # Giving the Server's info if admin

    cpu = ""
    ram = ""
    disk = ""

    if request.user.is_superuser:
        import psutil
        hdd = psutil.disk_usage('/')
        mem = psutil.virtual_memory()
        disk = str(int(round(hdd.free / (2**30),0))) + " GB Free"  
        cpu = psutil.cpu_percent()
        ram = mem.percent


    try:
        upload_status = request.GET['upload_stauts']
        context = {'upload_status':upload_status, 'size':size, 'total_files':total_files, 'filenames':show_file}
        return render(request, 'dashboard/index.html', context)

    except:
        context = {'cpu':cpu, 'ram':ram, 'disk':disk, 'size':size, 'total_files':total_files, 'filenames':show_file}
        return render(request, 'dashboard/index.html', context)



# Upload form
@login_required
def Form(request):
    return render(request, "dashboard/upload.html", {})

@login_required
def Upload(request):

    if request.POST:

        redirect_url = request.POST.get("redirect", "")

        profile = Profile.objects.filter(user=request.user).first()
        folder_id = str(profile.folder_id)

        # To Generate random share id
        appha = 'abcde0fghij1klmnop4q2rst3uvwx5yzABC6DEFGHI7JKLM8NOP9QRS0TUVWXYZ'

        def process(f):

            file = open(str(BASE_DIR) + '/uploads/' + folder_id + '/' + str(f.name), 'wb+')
            for chunk in f.chunks():
                file.write(chunk)

            code = ""

            for i in range(26):
                x = random.randint(0, 62)
                code += appha[x]


            # Checking if the file with that filename already exists...

            try:
                file = File.objects.get(file_name=f.name)

            except:
            
                file = File(user = request.user,
                            file_name = f.name,
                            file_size = os.path.getsize(str(BASE_DIR) + '/uploads/' + folder_id + '/' + str(f.name)),
                            share_id = code,
                            server_location = '/uploads/' + folder_id + '/' + str(f.name)
                            )

                file.save()

        #######


        for count, x in enumerate(request.FILES.getlist("files")):
            process(x)

        if redirect_url:
            return HttpResponseRedirect(redirect_url+'?upload_stauts=complete')


        try:
            response = 'Files Uploaded Successfully' if count > 2 else 'File Uploaded Successfully'
        except:
            response = 'Files Uploaded Successfully'

        return render(request, "dashboard/upload.html", {'response':response, 'upload_status':'done'})

    else:
        redirect('cloud-dashboard')


@login_required
def show_files(request):

    profile = Profile.objects.filter(user=request.user).first()
    folder_id = str(profile.folder_id)


    # Checking if the user has a query for a specific filename
    try:
        query = request.GET['query']

        all_files = File.objects.filter(user=request.user).order_by('-data_last_modified').filter(in_bin = False)
        all_files = all_files.filter(file_name__icontains = query)

        total_files = len(next(os.walk(str(BASE_DIR) + '/uploads/' + folder_id + '/'))[2]) 
        size = get_size_format(get_directory_size(str(BASE_DIR) + '/uploads/' + folder_id + '/'))

        return render(request, "dashboard/show_files.html", {'size':size, 'total_files':total_files, 'filenames':all_files, 'query':query})

    except:
        pass
    # --------------------------------------------------------------------------------- #


    # Getting all the files

    all_files = File.objects.filter(user=request.user).order_by('-data_last_modified').filter(in_bin = False)
    total_files = len(next(os.walk(str(BASE_DIR) + '/uploads/' + folder_id + '/'))[2]) 

    size = get_size_format(get_directory_size(str(BASE_DIR) + '/uploads/' + folder_id + '/'))
              
    return render(request, "dashboard/show_files.html", {'size':size, 'total_files':total_files, 'filenames':all_files})


@login_required
def delete_file(request):

    try:
        in_bin = request.GET['inbin']
        if in_bin == 'True':
            profile = Profile.objects.get(user=request.user)
            folder_id = str(profile.folder_id)
            filename = request.GET['filename']

            try:
                os.remove(str(BASE_DIR) + '/uploads/' + folder_id + '/bin/' + filename)
                File.objects.get(file_name = filename).delete()
                return render(request, "dashboard/deleted.html", {'deleted':"&#9989; The file has been permanently been deleted!"})
            except:
                return render(request, "dashboard/deleted.html", {'deleted':"<i style='color:red' class='material-icons'>error</i>  The file didn't Exist!<hr>Maybe it has already been deleted! Or you are not the owner of the file"})

    except:

        profile = Profile.objects.filter(user=request.user).first()
        folder_id = str(profile.folder_id)

        if request.GET:
            filename = request.GET['filename']
            try:
                os.mkdir(str(BASE_DIR) + '/uploads/' + folder_id + '/' + 'bin/')
            except:
                pass

            try:
                shutil.move(str(BASE_DIR) + '/uploads/' + folder_id + '/' + filename, str(BASE_DIR) + '/uploads/' + folder_id + '/bin/' + filename)
                file = File.objects.get(file_name = filename)
                file.in_bin = True
                file.save()

                return render(request, "dashboard/deleted.html", {'deleted':"&#9989; The file was moved to bin!"})
            except:
                return render(request, "dashboard/deleted.html", {'deleted':"<i style='color:red' class='material-icons'>error</i> <b>The file didn't Exist!</b><hr>Maybe it has already been deleted! Or you are not the owner of the file"})


@login_required
def view_file(request):

    try:
        in_bin = request.GET['inbin']
        if in_bin == 'True':
            profile = Profile.objects.filter(user=request.user).first()
            folder_id = str(profile.folder_id)
            filename = request.GET['filename']
            file = '/uploads/' + folder_id + '/bin/' + filename

            return HttpResponseRedirect(file)

    except:

        if request.GET:
            profile = Profile.objects.filter(user=request.user).first()
            folder_id = str(profile.folder_id)
            filename = request.GET['filename']
            file = '/uploads/' + folder_id + '/' + filename

            return HttpResponseRedirect(file)


def info(request):
    return render(request, 'info.html')


def contact_us(request):
    return render(request, 'contact.html')

@login_required
def bin_file(request):
    profile = Profile.objects.filter(user=request.user).first()
    folder_id = str(profile.folder_id)

    try:
        os.mkdir(str(BASE_DIR) + "/uploads/" + str(folder_id) + "/bin")
    except:
        pass


    # Checking if the user has a query for a specific filename
    try:
        query = request.GET['query']

        all_files = File.objects.filter(user=request.user).order_by('-data_last_modified').filter(in_bin=True)
        all_files = all_files.filter(file_name__icontains = query)


        total_files = len(next(os.walk(str(BASE_DIR) + '/uploads/' + folder_id + '/'))[2]) 
        size = get_size_format(get_directory_size(str(BASE_DIR) + '/uploads/' + folder_id + '/'))

        return render(request, "dashboard/bin_files.html", {'size':size, 'total_files':total_files, 'filenames':all_files, 'query':query})

    except:
        pass
    # --------------------------------------------------------------------------------- #


    all_files = File.objects.filter(user=request.user).order_by('-data_last_modified').filter(in_bin=True)

    # Total numbers of file
    total_files = len(next(os.walk(str(BASE_DIR) + '/uploads/' + folder_id + '/bin/'))[2]) 

    size = get_size_format(get_directory_size(str(BASE_DIR) + '/uploads/' + folder_id + '/'))
              
    return render(request, "dashboard/bin_files.html", {'size':size, 'total_files':total_files, 'filenames':all_files})


@login_required
def empty_bin(request):
    profile = Profile.objects.filter(user=request.user).first()
    folder_id = str(profile.folder_id)

    try:
        files = glob.glob(str(BASE_DIR) + "/uploads/" + str(folder_id) + "/bin/*")
        for f in files:
            os.remove(f)
            File.objects.get(file_name = os.path.basename(f)).delete()
        return render(request, "dashboard/bin_files.html", {'status':'&#9989; Successfully emptied bin!'})
    except:
        return render(request, "dashboard/bin_files.html", {'status':"<i style='color:red' class='material-icons'>error</i> Error occured while emptying bin"})



def backup(request):
    return render(request, "dashboard/backup.html")

@login_required
def share_file(request, str):

    # Checking if the request was to turn on the linksharing
    try:
        status = request.GET['linksharing']

        profile = Profile.objects.get(user=request.user)
        folder_id = profile.folder_id

        file = File.objects.get(file_name=str)
        file.shared = True
        file.save()

        link = "https://fileshare.lissankoirala.ml/uploads/" + folder_id + '/' + str + '?token=' + file.share_id

        link_message = "<br><br><b>Link Copied and file sharing turned on for this file!</b>"

        return render(request, "dashboard/share_file.html", {'filename':str, 'link':link, 'link_message':link_message})
    
    except:
        pass


    try: # Checking if the user had asked to send the link via email
        
        email_id = request.POST.get("email", "")
        message = request.POST.get("message", "")

        if email_id != "":

            ##############################################

            profile = Profile.objects.get(user=request.user)
            folder_id = profile.folder_id

            file = File.objects.get(file_name=str)
            file.shared = True
            file.save()

            link = "https://fileshare.lissankoirala.ml/uploads/" + folder_id + '/' + str + '?token=' + file.share_id

            ##############################################

            subject = request.user.username + " Sent you a File Link via FileShare"

            if message != "":
                message = "Sender : " + request.user.username + "<hr><u>Message</u><br>" + message
            else:
                message = "Sender : " + request.user.username


            ##############################################################

            html_message = render_to_string('dashboard/file_link_email_template.html', {'link':link, 'username': request.user, 'message':message})
            plain_message = strip_tags(html_message)

            mail.send_mail(subject, plain_message, 'auth.nayasambandha@gmail.com', [email_id], html_message=html_message)


            return render(request, "dashboard/email_sent_with_link.html", {'filename':str, 'email':email_id, 'message':message})


    except Exception as e:

        print(e)
        


    profile = Profile.objects.get(user=request.user)
    folder_id = profile.folder_id

    file = File.objects.get(file_name=str)

    link = "https://fileshare.lissankoirala.ml/uploads/" + folder_id + '/' + str + '?token=' + file.share_id

    return render(request, "dashboard/share_file.html", {'filename':str, 'link':link})


def share_file_email(request, str):

    if request.POST:

        try:

            email_id = request.POST.get("email", "")
            message = request.POST.get("message", "")

            ##############################################

            file = File.objects.get(file_name=str)
            user = file.user
            
            profile = Profile.objects.get(user=request.user)
            folder_id = profile.folder_id

            if user == request.user:

                subject = request.user.username + " Sent you a File via FileShare"

                if message != "":
                    message = "Sender : " + request.user.username + "<hr><u>Message</u><br>" + message
                else:
                    message = "Sender : " + request.user.username + "<hr><u>Message</u><br>This File was sent to you via FileShare"


                email = EmailMessage(subject, message, 'auth.nayasambandha@gmail.com', [email_id])
                email.content_subtype = 'html'

                file = open(BASE_DIR + "/uploads/" + folder_id + '/' + str, "rb")
                email.attach(str, file.read(), "multipart/form-data")

                email.send()


                return render(request, "dashboard/file_sent_by_mail.html", {'filename':str, 'email':email_id, 'message':message})

            else:

                return render(request, "dashboard/404.html")
                

        except Exception as e:
            print(e)
            
            return render(request, "dashboard/file_sent_by_mail_error.html", {'filename':str})

    else:
        return render(request, "dashboard/404.html")





def shared_files(request):
    profile = Profile.objects.get(user=request.user)
    folder_id = profile.folder_id

    file = File.objects.filter(user = request.user).filter(shared = True)

    return render(request, "dashboard/shared_files.html", {'filenames':file, 'folder':folder_id})


def turn_sharing_off(request, str):

    file = File.objects.get(file_name=str)
    file.shared = False
    file.save()

    file = File.objects.filter(user = request.user).filter(shared = True)

    return render(request, "dashboard/shared_files.html", {'filenames':file, 'success':'Sharing has been turned off for : ' + str})
