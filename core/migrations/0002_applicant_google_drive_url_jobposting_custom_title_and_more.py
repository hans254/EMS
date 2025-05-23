# Generated by Django 4.2 on 2025-03-11 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicant',
            name='google_drive_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobposting',
            name='custom_title',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='jobposting',
            name='requirements',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='jobposting',
            name='title',
            field=models.CharField(choices=[('Frontend Engineer', 'Frontend Engineer/Developer'), ('Backend Engineer', 'Backend Engineer/Developer'), ('Fullstack Developer', 'Fullstack Developer'), ('Data Scientist', 'Data Scientist'), ('Cybersecurity Analyst', 'Cybersecurity Analyst'), ('Software Engineer', 'Software Engineer'), ('IT Support Specialist', 'IT Support Specialist'), ('DevOps Engineer', 'DevOps Engineer'), ('Other', 'Other')], default='Frontend Engineer', max_length=200),
        ),
    ]
