# Generated by Django 3.2.3 on 2021-07-03 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('match', '0006_match_history_filepath'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='history_filepath',
            field=models.FilePathField(null=True),
        ),
    ]
