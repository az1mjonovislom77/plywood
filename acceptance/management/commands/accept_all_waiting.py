import sys
from django.core.management.base import BaseCommand
from acceptance.models import Acceptance
from acceptance.service.acceptance_workflow import AcceptanceWorkflowService
from user.models import User


def _make_utf8_safe(stream):
    if hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    return stream


class Command(BaseCommand):
    help = 'Accepts all acceptances currently in WAITING status, applying their count/price to the related product.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user accepting the acceptances (defaults to the first superuser)',
            required=False
        )

    def handle(self, *args, **kwargs):
        _make_utf8_safe(sys.stdout)
        _make_utf8_safe(sys.stderr)

        user_id = kwargs.get('user_id')

        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found."))
                return
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()

            if not user:
                self.stdout.write(self.style.ERROR("No users found in the database. Please specify a user ID."))
                return

        waiting_ids = list(
            Acceptance.objects.filter(acceptance_status=Acceptance.AcceptanceStatus.WAITING)
            .order_by('id').values_list('id', flat=True)
        )

        self.stdout.write(f"Found {len(waiting_ids)} acceptances in WAITING status.")

        success_count = 0
        error_count = 0

        for acceptance_id in waiting_ids:
            try:
                AcceptanceWorkflowService.accept(acceptance_id, user)
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Acceptance #{acceptance_id}: Failed to accept. Error: {str(e)}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Accepted: {success_count}, Errors: {error_count}"))
