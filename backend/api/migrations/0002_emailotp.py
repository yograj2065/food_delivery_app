# Generated migration for EmailOTP model
# Adds the email_otp table used by the OTP authentication system.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Depends on the initial migration that created all existing tables
        ('api', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailOTP',
            fields=[
                # Auto primary key
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                # FK to Django's built-in User model
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='otps',
                    to=settings.AUTH_USER_MODEL,
                )),
                # The 6-digit OTP code stored as a string
                ('otp', models.CharField(max_length=6)),
                # Distinguishes registration OTPs from login OTPs
                ('purpose', models.CharField(
                    choices=[('register', 'Registration'), ('login', 'Login')],
                    max_length=10,
                )),
                # Timestamp used to enforce the 5-minute expiry window
                ('created_at', models.DateTimeField(auto_now_add=True)),
                # Tracks failed verification attempts (max 5)
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                # Prevents OTP reuse after successful verification
                ('is_verified', models.BooleanField(default=False)),
            ],
            options={
                # Most recent OTP first in querysets
                'ordering': ['-created_at'],
            },
        ),
    ]
