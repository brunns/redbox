# Generated by Django 5.0.7 on 2024-08-08 08:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('redbox_core', '0028_aisettings'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ChatHistory',
            new_name='Chat',
        ),
        migrations.AlterModelOptions(
            name='chat',
            options={},
        ),
        migrations.RenameField(
            model_name='chatmessage',
            old_name='chat_history',
            new_name='chat',
        ),
    ]
