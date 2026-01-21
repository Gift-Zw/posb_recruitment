# Generated manually to fix employee_profiles table schema

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_add_missing_employee_profile_columns'),
    ]

    operations = [
        # Drop old columns that shouldn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    -- Drop address column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='address'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN address;
                    END IF;
                    
                    -- Drop date_of_birth column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='date_of_birth'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN date_of_birth;
                    END IF;
                    
                    -- Drop nationality column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='nationality'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN nationality;
                    END IF;
                    
                    -- Drop office_location column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='office_location'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN office_location;
                    END IF;
                    
                    -- Drop emergency_contact_name column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='emergency_contact_name'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN emergency_contact_name;
                    END IF;
                    
                    -- Drop emergency_contact_phone column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='emergency_contact_phone'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN emergency_contact_phone;
                    END IF;
                    
                    -- Drop education column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='education'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN education;
                    END IF;
                    
                    -- Drop internal_experience column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='internal_experience'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN internal_experience;
                    END IF;
                    
                    -- Drop additional_info column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='additional_info'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN additional_info;
                    END IF;
                    
                    -- Drop is_active column if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='is_active'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN is_active;
                    END IF;
                    
                    -- Drop employee_id column if it exists (replaced by ec_number)
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='employee_id'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN employee_id;
                    END IF;
                    
                    -- Drop position column if it exists (replaced by job_title)
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='employee_profiles' AND column_name='position'
                    ) THEN
                        ALTER TABLE employee_profiles DROP COLUMN position;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
