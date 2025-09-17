# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='github_url',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='facebook_url',
            field=models.URLField(blank=True),
        ),
    ]

