# Generated by Django 4.1.7 on 2023-04-21 07:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workwhere', '0002_floorplan'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='FloorPlan',
            new_name='Floor',
        ),
    ]
