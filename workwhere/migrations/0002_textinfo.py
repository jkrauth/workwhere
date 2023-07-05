# Generated by Django 4.1.7 on 2023-07-05 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workwhere', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='HowTo', max_length=80)),
                ('content', models.TextField(default='This is some help text')),
                ('order', models.PositiveIntegerField()),
            ],
        ),
    ]