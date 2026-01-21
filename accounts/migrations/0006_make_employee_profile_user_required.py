# Generated manually to make user field required

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_add_user_field_to_employee_profile'),
    ]

    operations = [
        # Delete any EmployeeProfile records without a user (orphaned records)
        migrations.RunSQL(
            sql="""
                DELETE FROM employee_profiles WHERE user_id IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        # Make user_id non-nullable
        migrations.RunSQL(
            sql="""
                ALTER TABLE employee_profiles 
                ALTER COLUMN user_id SET NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles 
                ALTER COLUMN user_id DROP NOT NULL;
            """
        ),
    ]
