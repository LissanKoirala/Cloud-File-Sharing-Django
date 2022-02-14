from django.contrib import admin
from django.urls import path, include
from upload import views as upload_views
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

admin.site.site_header = "File Share"
admin.site.site_title = "File Share"
admin.site.index_title = "File Share Admin Dashboard"

# For security check for the file
from users.models import Profile
from django.urls import re_path
from django.views.static import serve
from django.shortcuts import render, redirect

import datetime
from upload.models import File



# To autheticate users before serving files
@login_required
def file_permission(request, path, file_root=None):
    profile = Profile.objects.filter(user=request.user).first() # Getting their profile
    folder_id = str(profile.folder_id) # Logged in user folder id

    try:
        requested_folder = path.split('/')[0] # Requested folder id
    except:
        return render(request, "dashboard/404.html")

    try:
        requested_filename = path.split('/')[1] # Requested folder id
    except:
        return render(request, "dashboard/404.html")

    if folder_id == requested_folder: # If the requested folder id and the user id is the same server the file

        requested_filename = path.split('/')[1]

        # Changing the last viewed of the file
        file = File.objects.get(file_name=requested_filename)
        file.data_last_modified = datetime.datetime.now()

        print(datetime.datetime.now())


        file.save()

        return serve(request, path, file_root)
    
    elif requested_folder == 'public': # If the requested file is in public directory it is accessable by everyone
        return serve(request, path, file_root)

    else:
        
        try: # Checking if the use has the token of the file 
            user_token = request.GET['token']
            print(user_token)

            file = File.objects.get(file_name=requested_filename)
            token = file.share_id
            shared = file.shared

            if user_token == token: # Checking if the token that the user has is correct

                if shared: # Checking if the file shared mode is on or not
                    return serve(request, path, file_root)

                else:
                    return render(request, "dashboard/shared_off.html") # If shared no on say you can no longer view this file

            else:
                print("The token didn't match token given " + user_token + " real token " + token)
                return render(request, "dashboard/file_not_allowed.html") # If token doesn't match, not allowed




        except Exception as e: # If the use doesn't have token of the file then he is not allowed to view it
            print("ERROR " + str(e))
            return render(request, "dashboard/file_not_allowed.html")





urlpatterns = [
    path('profile/', user_views.profile, name='profile'),
    path('register', user_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('activate/', user_views.account_activation, name='activate'),

    path('contact-us', upload_views.contact_us, name='contact'),

    path('cloud/dashboard/', upload_views.dashboard, name='cloud-dashboard'),
    path('local-devices/dashboard/', upload_views.dashboard, name='local-devices-dashboard'),

    path('admin/', admin.site.urls),
    path('', include('devices.urls')),

    path('info/', upload_views.info, name='info'),

    path('cloud/dashboard/upload/', upload_views.Form, name='upload'),
    path('cloud/dashboard/upload_complete/', upload_views.Upload, name='upload-request'),
    path('cloud/dashboard/show_files/', upload_views.show_files, name='view'),

    path('cloud/dashboard/share/<str:str>/', upload_views.share_file, name='share-file'),
    path('cloud/dashboard/shared_files/', upload_views.shared_files, name='shared-files'),

    path('cloud/dashboard/share/off/<str:str>', upload_views.turn_sharing_off, name='turn-off-sharing'),

    path('cloud/dashboard/share/email/<str:str>/', upload_views.share_file_email, name='share-file-email'),

    path('cloud/dashboard/delete/', upload_views.delete_file, name='delete'),
    path('cloud/dashboard/view/', upload_views.view_file, name='request-view'),
    path('cloud/dashboard/bin/', upload_views.bin_file, name='bin'),
    path('cloud/dashboard/empty-bin/', upload_views.empty_bin, name='empty-bin'),

    path('cloud/dashboard/backup/', upload_views.backup, name='backup'),

    # To verify users before serving the media files...
    re_path(r'^{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:]), file_permission, {'file_root': settings.MEDIA_ROOT}),

    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('password_change/', 
        auth_views.PasswordChangeView.as_view(success_url='/', template_name='registration/password_change.html'), 
        name='password_change'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "devices.views.view_404"