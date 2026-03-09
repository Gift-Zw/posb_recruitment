from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='force_password_reset',
            field=models.BooleanField(
                default=False,
                help_text='Require user to change password before accessing the portal.',
            ),
        ),
    ]
