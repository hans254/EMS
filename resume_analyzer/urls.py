"""
URL configuration for resume_analyzer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path("job_posting_create/", views.job_posting_create, name="job_posting_create"),
    path('upload-resumes/<int:job_id>/', views.upload_resumes, name='upload_resumes'),
    path('recruitment_list/', views.recruitment_list, name='recruitment_list'),
    path('send-invitations/<int:job_id>/', views.send_invitations, name='send_invitations'),
    path("delete_items/<int:pk>/", views.delete_items, name="delete_items"),
    path('job_detail/<str:pk>/', views.job_detail, name='job_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)