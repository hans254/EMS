from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mass_mail
from django.conf import settings
import os
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Applicant, JobPosting
from .utils import send_regret_email
from .models import JobPosting, Applicant, EmailInvitation
from .forms import JobPostingForm, ApplicantForm, EmailInvitationForm, JobSearchForm
from .utils import extract_text_from_pdf, extract_text_from_docx, extract_name_email, calculate_similarity
from django.core.paginator import Paginator
from django.http import JsonResponse
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from tkinter import Tk
from tkinter.filedialog import askdirectory
from io import FileIO
import re
from django.contrib.auth.decorators import login_required

# Path to your credentials file
CREDENTIALS_FILE = 'credentials.json'

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def extract_file_or_folder_id(url):
    """
    Extract the file or folder ID from a Google Drive URL.
    Supports multiple URL formats.
    """
    # Standard file URL format
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'file'

    # Folder URL format
    match = re.search(r'/drive/folders/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'folder'

    # Shortened URL format
    match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'file'

    # Shared URL format
    match = re.search(r'/uc\?export=download&id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'file'

    # If no match is found, raise an error
    raise ValueError("Invalid Google Drive URL. Could not extract file or folder ID.")


def download_file_from_google_drive(file_id, destination_folder):
    """Download a file from Google Drive using its file ID."""
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    try:
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id, fields='name').execute()
        file_name = file_metadata['name']

        # Create the destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)

        # Download the file in chunks
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(destination_folder, file_name)
        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")

        return file_path
    except HttpError as e:
        raise Exception(f"Google Drive API error: {str(e)}")
    except Exception as e:
        raise Exception(f"An error occurred while downloading the file: {str(e)}")


def list_files_in_folder(folder_id):
    """List all files in a Google Drive folder."""
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    try:
        # Query files in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        return files
    except HttpError as e:
        raise Exception(f"Google Drive API error: {str(e)}")
    except Exception as e:
        raise Exception(f"An error occurred while listing files: {str(e)}")


@login_required
def recruitment_list(request):
    header = 'List of Posted Jobs'
    queryset = JobPosting.objects.all().order_by("-created_at")
    form = JobSearchForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        title = form.cleaned_data.get('title')
        # item_name = form.cleaned_data.get('item_name')

        if title:
            queryset = queryset.filter(title=title) 

    # Pagination
    paginator = Paginator(queryset, 5)
    page_number = request.GET.get('page')
    queryset = paginator.get_page(page_number)

    context = {
        'form': form,
        'queryset': queryset,
        'header': header,
    }

    return render(request, 'core/recruitment_list.html', context)

@login_required
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


from django.core.mail import send_mail
from django.conf import settings

@login_required
def upload_resumes(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    form = ApplicantForm()

    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES)
        resumes = request.FILES.getlist('resumes')
        google_drive_url = request.POST.get('url', '').strip()

        # Validate form before accessing cleaned_data
        if form.is_valid():
            drive_url = form.cleaned_data.get('drive_url', '')
            destination_folder = form.cleaned_data.get('destination_folder', '')

            # --- Handling Google Drive Resume Download ---
            if drive_url:
                if not destination_folder:
                    messages.error(request, 'Select folder first before proceeding to download.')
                    return redirect('upload_resumes', job_id=job.id)

                try:
                    resource_id, resource_type = extract_file_or_folder_id(drive_url)

                    if resource_type == 'file':
                        file_path = download_file_from_google_drive(resource_id, destination_folder)
                        messages.success(request, 'Resumes have been downloaded successfully.')
                    elif resource_type == 'folder':
                        files = list_files_in_folder(resource_id)
                        downloaded_files = [
                            download_file_from_google_drive(file['id'], destination_folder) for file in files
                        ]
                        messages.success(request, f'{len(downloaded_files)} resumes have been downloaded successfully.')

                    # **Clear drive_url field after successful download**
                    form = ApplicantForm(initial={'drive_url': '', 'destination_folder': destination_folder})

                except ValueError as e:
                    messages.error(request, f'Error: {str(e)}')
                except Exception as e:
                    messages.error(request, f'An error occurred: {str(e)}')

        # --- Handling Google Drive URL Upload ---
        elif google_drive_url:
            try:
                applicant = Applicant.objects.create(job=job, name="Unknown", email="Unknown", url=google_drive_url)
                result = import_resumes_from_drive(applicant)

                if "error" in result:
                    messages.error(request, result["error"])
                else:
                    messages.success(request, result["success"])
            except Exception as e:
                messages.error(request, f'Error importing resumes from Google Drive: {str(e)}')

        # --- Handling Direct File Upload (Local Resumes) ---
        if resumes:
            for resume_file in resumes:
                try:
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
                except Exception as e:
                    messages.error(request, f'Error processing {resume_file.name}: {str(e)}')

            messages.success(request, 'Resumes uploaded successfully')
            return redirect('upload_resumes', job_id=job.id)

    # Fetch all applicants
    all_candidates = Applicant.objects.filter(job=job).order_by('-score')
    top_candidates = all_candidates[:job.required_candidates]

  
    # Pagination
    paginator = Paginator(all_candidates, 3)
    page_number = request.GET.get('page')
    queryset = paginator.get_page(page_number)

    context = {
        'job': job,
        'form': form,  # Ensure updated form is sent to the template
        'queryset': queryset,
        'top_candidates': top_candidates,
        'all_candidates': all_candidates
    }
    return render(request, 'core/upload_resumes.html', context)

# @login_required
def select_folder(request):
    if request.method == 'GET':
        root = Tk()
        root.withdraw()
        folder_path = askdirectory(title="Select Destination Folder")
        root.destroy()

        if folder_path:
            return JsonResponse({'folder_path': folder_path})
        else:
            return JsonResponse({'error': 'No folder selected'}, status=400)

@login_required
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

@login_required
def delete_items(request, pk):
    queryset = JobPosting.objects.get(id=pk)
    if request.method == 'POST':
        queryset.delete()
        messages.success(request, 'Deleted Successfully')
        return redirect('recruitment_list')
    return render(request, 'core/delete_items.html')  

@login_required
def job_detail(request, pk):
    queryset = JobPosting.objects.get(id=pk)
    context = {
        'queryset': queryset,
    }
    return render(request, 'core/job_detail.html', context)  

@login_required
def unqualified_applicants():
    return render(request, 'core/unqualified_applicants.html')




def send_regret_emails(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    
    # Define the qualification threshold (e.g., 50%)
    threshold = 50.0

    # Get unqualified applicants
    unqualified_candidates = Applicant.objects.filter(job=job, score__lt=threshold)

    if unqualified_candidates.exists():
        for applicant in unqualified_candidates:
            send_regret_email(applicant)  # Use the utility function

        messages.success(request, f"Regret emails sent to {unqualified_candidates.count()} unqualified candidates.")
    else:
        messages.info(request, "No unqualified candidates found.")

    return redirect("upload_resumes", job_id=job.id)
