# Generated manually to fix missing columns in employee_profiles table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_make_employee_profile_user_required'),
    ]

    operations = [
        # Add ec_number column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='ec_number'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD COLUMN ec_number varchar(50) NULL UNIQUE;
                        CREATE INDEX IF NOT EXISTS employee_pr_ec_numb_173b98_idx ON employee_profiles (ec_number);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles DROP COLUMN IF EXISTS ec_number;
                DROP INDEX IF EXISTS employee_pr_ec_numb_173b98_idx;
            """
        ),
        # Add phone_number column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='phone_number'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD COLUMN phone_number varchar(20) DEFAULT '' NOT NULL;
                        ALTER TABLE employee_profiles ALTER COLUMN phone_number DROP DEFAULT;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles DROP COLUMN IF EXISTS phone_number;
            """
        ),
        # Add department column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='department'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD COLUMN department varchar(200) DEFAULT '' NOT NULL;
                        ALTER TABLE employee_profiles ALTER COLUMN department DROP DEFAULT;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles DROP COLUMN IF EXISTS department;
            """
        ),
        # Add job_title column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='job_title'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD COLUMN job_title varchar(200) DEFAULT '' NOT NULL;
                        ALTER TABLE employee_profiles ALTER COLUMN job_title DROP DEFAULT;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles DROP COLUMN IF EXISTS job_title;
            """
        ),
        # Add created_at column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='created_at'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD COLUMN created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL;
                        ALTER TABLE employee_profiles ALTER COLUMN created_at DROP DEFAULT;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles DROP COLUMN IF EXISTS created_at;
            """
        ),
        # Add updated_at column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='updated_at'
                    ) THEN
                        ALTER TABLE employee_profiles 
                        ADD COLUMN updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL;
                        ALTER TABLE employee_profiles ALTER COLUMN updated_at DROP DEFAULT;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE employee_profiles DROP COLUMN IF EXISTS updated_at;
            """
        ),
    ]
