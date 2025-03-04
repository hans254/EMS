# from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static
# from . import views

# urlpatterns = [
#     path('', views.job_posting_create, name='job_posting_create'),
#     path('upload-resumes/<int:job_id>/', views.upload_resumes, name='upload_resumes'),
#     path('send-invitations/<int:job_id>/', views.send_invitations, name='send_invitations'),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 