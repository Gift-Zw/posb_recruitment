from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0006_application_upload_status_cleanup"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="review_status",
            field=models.CharField(
                choices=[
                    ("PENDING_REVIEW", "Pending Review"),
                    ("APPROVED", "Approved"),
                    ("REJECTED", "Rejected"),
                ],
                default="PENDING_REVIEW",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="application",
            name="reviewed_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When HR approved or rejected the application",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="application",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_applications",
                to="accounts.user",
            ),
        ),
        migrations.AddIndex(
            model_name="application",
            index=models.Index(fields=["job_advert", "review_status"], name="applicatio_job_adv_901d03_idx"),
        ),
    ]
