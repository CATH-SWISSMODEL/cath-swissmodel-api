# Generated by Django 2.1.2 on 2018-10-25 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_selecttemplatetask_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='selecttemplatetask',
            name='remote_task_id',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]