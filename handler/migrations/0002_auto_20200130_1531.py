# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2020-01-30 21:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('handler', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registration',
            old_name='first_name',
            new_name='depto',
        ),
        migrations.RenameField(
            model_name='registration',
            old_name='last_name',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='contact',
            name='message',
        ),
        migrations.RemoveField(
            model_name='registration',
            name='contact_number',
        ),
    ]
