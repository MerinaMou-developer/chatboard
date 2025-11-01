# Generated manually to add access_level field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='access_level',
            field=models.CharField(
                choices=[('PUBLIC', 'All org members'), ('PRIVATE', 'Invite only'), ('MANAGER_ONLY', 'Manager/Admin only')],
                default='PUBLIC',
                max_length=12
            ),
        ),
    ]

