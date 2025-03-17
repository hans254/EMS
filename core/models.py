from django.db import models

class JobPosting(models.Model):
    title = models.CharField(max_length=200)
    requirements = models.TextField()
    required_candidates = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Applicant(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applicants')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    resume = models.FileField(upload_to='resumes/')
   # url = models.URLField(max_length=500, blank=True, null=True)
    score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.job.title}"


class EmailInvitation(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation for {self.job.title}" 