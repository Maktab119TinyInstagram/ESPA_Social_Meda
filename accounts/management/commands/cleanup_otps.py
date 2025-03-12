from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import OTP


class Command(BaseCommand):
    """
    Management command to clean up expired and used OTPs.
    """
    help = _('Clean up expired and used OTPs')

    def add_arguments(self, parser):
        """
        Add command arguments.
        """
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help=_('Delete OTPs older than this many days (default: 7)')
        )
        parser.add_argument(
            '--used',
            action='store_true',
            help=_('Delete only used OTPs')
        )
        parser.add_argument(
            '--expired',
            action='store_true',
            help=_('Delete only expired OTPs')
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help=_('Perform a dry run without deleting any OTPs')
        )

    def handle(self, *args, **options):
        """
        Handle the command.
        """
        days = options['days']
        used_only = options['used']
        expired_only = options['expired']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Build the queryset based on the options
        queryset = OTP.objects.filter(created_at__lt=cutoff_date)
        
        if used_only:
            queryset = queryset.filter(is_used=True)
        
        if expired_only:
            queryset = queryset.filter(expires_at__lt=timezone.now())
        
        # Count the OTPs to be deleted
        count = queryset.count()
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    _('Would delete %(count)d OTPs') % {'count': count}
                )
            )
        else:
            # Delete the OTPs
            queryset.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    _('Successfully deleted %(count)d OTPs') % {'count': count}
                )
            ) 