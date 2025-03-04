from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mass_mail
from django.conf import settings
from .models import JobPosting, Applicant, EmailInvitation
from .forms import JobPostingForm, ApplicantForm, EmailInvitationForm
from .utils import extract_text_from_pdf, extract_text_from_docx, calculate_similarity

def job_posting_create(request):
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save()
            return redirect('upload_resumes', job_id=job.id)
    else:
        form = JobPostingForm()
    return render(request, 'core/job_posting_form.html', {'form': form})

def upload_resumes(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    
    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.job = job
            
            # Extract text from resume
            resume_file = request.FILES['resume']
            if resume_file.name.endswith('.pdf'):
                resume_text = extract_text_from_pdf(resume_file)
            elif resume_file.name.endswith('.docx'):
                resume_text = extract_text_from_docx(resume_file)
            else:
                messages.error(request, 'Unsupported file format')
                return redirect('upload_resumes', job_id=job.id)
            
            # Calculate similarity score
            score = calculate_similarity(job.requirements, resume_text)
            applicant.score = score
            applicant.save()
            
            messages.success(request, 'Resume uploaded successfully')
            return redirect('upload_resumes', job_id=job.id)
    else:
        form = ApplicantForm()
    
    # Get top candidates
    top_candidates = Applicant.objects.filter(job=job).order_by('-score')[:job.required_candidates]
    
    context = {
        'job': job,
        'form': form,
        'top_candidates': top_candidates,
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
            
            # Prepare emails
            emails = []
            for candidate in top_candidates:
                email = (
                    invitation.subject,
                    invitation.message,
                    settings.DEFAULT_FROM_EMAIL,
                    [candidate.email],
                )
                emails.append(email)
            
            # Send emails
            send_mass_mail(emails)
            messages.success(request, 'Invitations sent successfully')
            return redirect('job_posting_create')
    else:
        form = EmailInvitationForm()
    
    context = {
        'job': job,
        'form': form,
        'top_candidates': top_candidates,
    }
    return render(request, 'core/send_invitations.html', context)