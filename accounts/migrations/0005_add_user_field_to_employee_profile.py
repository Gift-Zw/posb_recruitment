# Generated manually to fix missing user_id column

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_employeeprofile_department_employeeprofile_job_title'),
    ]

    operations = [
        # Add user field - check if column exists first using RunSQL
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='user_id'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD COLUMN user_id bigint NULL;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles DROP COLUMN IF EXISTS user_id;
            """
        ),
        # Add foreign key constraint if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name='employee_profiles_user_id_a490e3b4_fk_users_id'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD CONSTRAINT employee_profiles_user_id_a490e3b4_fk_users_id 
                        FOREIGN KEY (user_id) REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles 
                DROP CONSTRAINT IF EXISTS employee_profiles_user_id_a490e3b4_fk_users_id;
            """
        ),
        # Add unique constraint if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name='employee_profiles_user_id_key'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD CONSTRAINT employee_profiles_user_id_key UNIQUE (user_id);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles 
                DROP CONSTRAINT IF EXISTS employee_profiles_user_id_key;
            """
        ),
    ]
