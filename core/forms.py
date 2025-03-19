from django import forms
from .models import JobPosting, Applicant, EmailInvitation

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['title', 'requirements', 'required_candidates']
        widgets = {
            'requirements': forms.Textarea(attrs={'rows': 5}),
        }
    def __init__(self, *args, **kwargs):
        super(JobPostingForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})



class ApplicantForm(forms.ModelForm):
    drive_url = forms.URLField(
        label='Google Drive URL',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Google Drive URL',
            'aria-label': 'Google Drive URL',
            'aria-describedby': 'drive-url-help'
        })
    )
    destination_folder = forms.CharField(
        label='Destination Folder',
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Applicant
        fields = ['drive_url', 'destination_folder']


class EmailInvitationForm(forms.ModelForm):
    class Meta:
        model = EmailInvitation
        fields = ['subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

class JobSearchForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['title']