from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mass_mail
from django.conf import settings
import os
from .models import JobPosting, Applicant, EmailInvitation
from .forms import JobPostingForm, ApplicantForm, EmailInvitationForm
from .utils import extract_text_from_pdf, extract_text_from_docx, extract_name_email, calculate_similarity
from django.core.paginator import Paginator


def job_posting_create(request):
    header = 'Create Job Posting'
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save()
            return redirect('upload_resumes', job_id=job.id)
    else:
        form = JobPostingForm()
    return render(request, 'core/job_posting_form.html', {'form': form})

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

def upload_resumes(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)

    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES)
        resumes = request.FILES.getlist('resumes')

        if resumes:
            for resume_file in resumes:
                if resume_file.name.endswith('.pdf'):
                    resume_text = extract_text_from_pdf(resume_file)
                elif resume_file.name.endswith('.docx'):
                    resume_text = extract_text_from_docx(resume_file)
                else:
                    messages.error(request, f'Unsupported file format: {resume_file.name}')
                    continue
                name, email = extract_name_email(resume_text)
                if not name or not email:
                    messages.warning(request, f'Could not extract name and email from {resume_file.name}')
                    continue
                score = calculate_similarity(job.requirements, resume_text)
                Applicant.objects.create(
                    job=job,
                    name=name,
                    email=email,
                    resume=resume_file,
                    score=score
                )

            messages.success(request, 'Resumes uploaded successfully')
            return redirect('upload_resumes', job_id=job.id)
    
    else:
        form = ApplicantForm()

    all_candidates = Applicant.objects.filter(job=job).order_by('-score')
    top_candidates = all_candidates[:job.required_candidates]

    queryset = all_candidates  
    paginator = Paginator(queryset, 3)
    page_number = request.GET.get('page')
    queryset = paginator.get_page(page_number)

    context = {
        'job': job,
        'form': form,
        'queryset': queryset,
        'top_candidates': top_candidates,
        'all_candidates': all_candidates
    }
    return render(request, 'core/upload_resumes.html', context)


def send_invitations(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    top_candidates = Applicant.objects.filter(job=job).order_by('-score')[:job.required_candidates]
    
    if request.method == 'POST':
        form = EmailInvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.job = job
            invitation.save()

            emails = []
            for candidate in top_candidates:
                cleaned_email = candidate.email.strip().rstrip('.')
                
                if '@' not in cleaned_email or '.' not in cleaned_email.split('@')[-1]:
                    messages.error(request, f"Invalid email address: {cleaned_email}")
                    continue
                
                email = (
                    invitation.subject,
                    invitation.message,
                    settings.DEFAULT_FROM_EMAIL,
                    [cleaned_email],
                )
                emails.append(email)
            
            if emails:
                try:
                    send_mass_mail(emails, fail_silently=False)
                    messages.success(request, 'Invitations sent successfully')
                except Exception as e:
                    messages.error(request, f"Error sending emails: {e}")
            else:
                messages.error(request, 'No valid email addresses to send invitations.')

            return redirect('job_posting_create')
    else:
        form = EmailInvitationForm()
    
    context = {
        'job': job,
        'form': form,
        'top_candidates': top_candidates,
    }
    return render(request, 'core/send_invitations.html', context)
