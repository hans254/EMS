from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path("job_posting_create/", views.job_posting_create, name="job_posting_create"),
    path("unqualified_applicants/", views.unqualified_applicants, name="unqualified_applicants"),
    path('upload-resumes/<int:job_id>/', views.upload_resumes, name='upload_resumes'),
    path('', views.recruitment_list, name='recruitment_list'),
    path('send-invitations/<int:job_id>/', views.send_invitations, name='send_invitations'),
    path("delete_items/<int:pk>/", views.delete_items, name="delete_items"),
    path('job_detail/<str:pk>/', views.job_detail, name='job_detail'),
    path('select-folder/', views.select_folder, name='select_folder'),
    path('send-regret-emails/<int:job_id>/', views.send_regret_emails, name='send_regret_emails'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)