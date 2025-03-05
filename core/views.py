from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mass_mail
from django.conf import settings
import os
from .models import JobPosting, Applicant, EmailInvitation
from .forms import JobPostingForm, ApplicantForm, EmailInvitationForm
from .utils import extract_text_from_pdf, extract_text_from_docx, extract_name_email, calculate_similarity


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
        resumes = request.FILES.getlist('resumes')  # Allow multiple file uploads

        if resumes:
            for resume_file in resumes:
                # Extract text from resume
                if resume_file.name.endswith('.pdf'):
                    resume_text = extract_text_from_pdf(resume_file)
                elif resume_file.name.endswith('.docx'):
                    resume_text = extract_text_from_docx(resume_file)
                else:
                    messages.error(request, f'Unsupported file format: {resume_file.name}')
                    continue

                # Extract name and email
                name, email = extract_name_email(resume_text)
                if not name or not email:
                    messages.warning(request, f'Could not extract name and email from {resume_file.name}')
                    continue

                # Calculate similarity score
                score = calculate_similarity(job.requirements, resume_text)

                # Save applicant details
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

    # Get all candidates sorted by score
    all_candidates = Applicant.objects.filter(job=job).order_by('-score')
    top_candidates = all_candidates[:job.required_candidates]

    context = {
        'job': job,
        'form': form,
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
            
            # Prepare emails
            emails = []
            for candidate in top_candidates:
                cleaned_email = candidate.email.strip().rstrip('.')  # Remove trailing spaces and periods
                
                if '@' not in cleaned_email or '.' not in cleaned_email.split('@')[-1]:
                    messages.error(request, f"Invalid email address: {cleaned_email}")
                    continue  # Skip invalid email
                
                email = (
                    invitation.subject,
                    invitation.message,
                    settings.DEFAULT_FROM_EMAIL,
                    [cleaned_email],  # Ensure cleaned email is used
                )
                emails.append(email)
            
            # Send emails if there are valid recipients
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

# def clean_resumes(request):
#     # Delete all records from the database
#     Applicant.objects.all().delete()
    
#     # Remove all resume files from the upload directory
#     upload_folder = os.path.join(settings.MEDIA_ROOT, 'resumes')  # Adjust folder name if needed
#     if os.path.exists(upload_folder):
#         for file in os.listdir(upload_folder):
#             file_path = os.path.join(upload_folder, file)
#             if os.path.isfile(file_path):
#                 os.remove(file_path)
    
#     return redirect('upload_resumes')  # Redirect back to