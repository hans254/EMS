from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mass_mail
from django.conf import settings
import os
from .models import JobPosting, Applicant, EmailInvitation
from .forms import JobPostingForm, ApplicantForm, EmailInvitationForm, JobSearchForm
from .utils import extract_text_from_pdf, extract_text_from_docx, extract_name_email, calculate_similarity
from django.core.paginator import Paginator


def recruitment_list(request):
    header = 'List of Posted Jobs'
    queryset = JobPosting.objects.all().order_by("-created_at")
    form = JobSearchForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        title = form.cleaned_data.get('title')
        # item_name = form.cleaned_data.get('item_name')

        if title:
            queryset = queryset.filter(title=title) 

        # if item_name:
        #     queryset = queryset.filter(item_name__icontains=item_name)

        # CSV Export Logic
        if form.cleaned_data.get('export_to_CSV', False):
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="List_of_Jobs.csv"'
            writer = csv.writer(response)
            writer.writerow(['CATEGORY', 'ITEM_NAME', 'QUANTITY'])

            for item in queryset:
                writer.writerow([item.category.name, item.item_name, item.quantity])
            return response

    # Pagination
    paginator = Paginator(queryset, 7)
    page_number = request.GET.get('page')
    queryset = paginator.get_page(page_number)

    context = {
        'form': form,
        'queryset': queryset,
        'header': header,
    }

    return render(request, 'core/recruitment_list.html', context)

def job_posting_create(request):
    header = 'Create Job Posting'
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save()
            return redirect('upload_resumes', job_id=job.id)
    else:
        form = JobPostingForm()

    context ={
        'form': form,
    }
    return render(request, 'core/job_posting_form.html', context)


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

            return redirect('recruitment_list')
    else:
        form = EmailInvitationForm()
    
    context = {
        'job': job,
        'form': form,
        'top_candidates': top_candidates,
    }
    return render(request, 'core/send_invitations.html', context)

def delete_items(request, pk):
    queryset = JobPosting.objects.get(id=pk)
    if request.method == 'POST':
        queryset.delete()
        messages.success(request, 'Deleted Successfully')
        return redirect('recruitment_list')
    return render(request, 'core/delete_items.html')    
