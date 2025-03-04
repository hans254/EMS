from django import forms
from .models import JobPosting, Applicant, EmailInvitation

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['title', 'requirements', 'required_candidates']
        widgets = {
            'requirements': forms.Textarea(attrs={'rows': 5}),
        }

class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['name', 'email', 'resume']

class EmailInvitationForm(forms.ModelForm):
    class Meta:
        model = EmailInvitation
        fields = ['subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }