from django.db import migrations, models


def map_legacy_statuses(apps, schema_editor):
    Application = apps.get_model("applications", "Application")
    Application.objects.filter(status__in=["SUBMITTED", "UNDER_REVIEW"]).update(status="PENDING_UPLOAD")
    Application.objects.filter(status="SHORTLISTED").update(status="UPLOADED_TO_ERP")
    Application.objects.filter(status="REJECTED").update(status="UPLOAD_FAILED")


def reverse_map_legacy_statuses(apps, schema_editor):
    Application = apps.get_model("applications", "Application")
    Application.objects.filter(status="PENDING_UPLOAD").update(status="SUBMITTED")
    Application.objects.filter(status="UPLOADED_TO_ERP").update(status="SHORTLISTED")
    Application.objects.filter(status="UPLOAD_FAILED").update(status="REJECTED")


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0005_applicationdata_external_application_id_and_more"),
    ]

    operations = [
        migrations.RunPython(map_legacy_statuses, reverse_map_legacy_statuses),
        migrations.RemoveField(
            model_name="application",
            name="ai_explanation",
        ),
        migrations.RemoveField(
            model_name="application",
            name="ai_ranking",
        ),
        migrations.RemoveField(
            model_name="application",
            name="ai_score",
        ),
        migrations.RemoveField(
            model_name="application",
            name="ai_shortlisted_at",
        ),
        migrations.RemoveIndex(
            model_name="application",
            name="application_status_f97bda_idx",
        ),
        migrations.AlterField(
            model_name="application",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING_UPLOAD", "Pending Upload"),
                    ("UPLOADED_TO_ERP", "Uploaded to ERP"),
                    ("UPLOAD_FAILED", "Upload Failed"),
                ],
                default="PENDING_UPLOAD",
                max_length=20,
            ),
        ),
    ]
