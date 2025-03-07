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
    resumes = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=True)

    class Meta:
        model = Applicant
        fields = ['resumes']

class EmailInvitationForm(forms.ModelForm):
    class Meta:
        model = EmailInvitation
        fields = ['subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

class JobSearchForm(forms.ModelForm):
    export_to_CSV = forms.BooleanField(required=False)
    class Meta:
        model = JobPosting
        fields = ['title']