# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteconfiguration',
            name='instagram_url',
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='facebook_url',
            field=models.URLField(blank=True, default='https://www.facebook.com/share/16JsHuJwh1/'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='twitter_url',
            field=models.URLField(blank=True, default='https://x.com/BarkhadleHabibo?t=dcVebF8tuOiQUGn67tC8dw&s=08'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='linkedin_url',
            field=models.URLField(blank=True, default='https://www.linkedin.com/in/habibo-barkadle-83428a213?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app'),
        ),
    ]
