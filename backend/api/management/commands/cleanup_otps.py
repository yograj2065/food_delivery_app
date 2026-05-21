"""
api/management/commands/cleanup_otps.py
────────────────────────────────────────
Django management command to purge stale OTP records.

Run manually:
    python manage.py cleanup_otps

Schedule with cron (every 15 minutes):
    */15 * * * * cd /path/to/backend && python manage.py cleanup_otps >> /var/log/otp_cleanup.log 2>&1
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import EmailOTP


class Command(BaseCommand):
    help = 'Delete expired and already-verified OTP records from the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show how many records would be deleted without actually deleting them.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Calculate the cutoff: anything older than 5 minutes is expired
        cutoff = timezone.now() - timezone.timedelta(minutes=5)

        # Target: expired OTPs OR already-verified OTPs
        stale_otps = EmailOTP.objects.filter(
            # Expired (created more than 5 minutes ago)
            created_at__lt=cutoff
        ) | EmailOTP.objects.filter(
            # Already used — no longer needed
            is_verified=True
        )

        count = stale_otps.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Would delete {count} stale OTP record(s).')
            )
            return

        stale_otps.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} stale OTP record(s).')
        )
