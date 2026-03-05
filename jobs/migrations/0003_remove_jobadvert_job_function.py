from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_country_educationlevel_delete_certification"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="jobadvert",
            name="job_adverts_job_fun_fd5e17_idx",
        ),
        migrations.RemoveField(
            model_name="jobadvert",
            name="job_function",
        ),
    ]
