# Generated by Django 3.2.3 on 2021-06-03 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_userinfo_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userinfo',
            name='username',
        ),
        migrations.AddField(
            model_name='userinfo',
            name='firstname',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='userinfo',
            name='lastname',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
