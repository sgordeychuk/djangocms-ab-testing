import random
import uuid
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from djangocms_ab_testing.models import ABTest, ABEvent


BROWSERS = ['Chrome', 'Safari', 'Firefox', 'Edge', 'Samsung Internet']
OS_LIST = ['Windows', 'Mac OS X', 'iOS', 'Android', 'Linux']
DEVICE_TYPES = ['desktop', 'mobile', 'tablet']
from djangocms_ab_testing.conf import get_valid_actions

ACTIONS = list(get_valid_actions())


class Command(BaseCommand):
    help = 'Seed dummy AB event data for dashboard testing'

    def add_arguments(self, parser):
        parser.add_argument('--events', type=int, default=500, help='Number of events to create')
        parser.add_argument('--days', type=int, default=30, help='Spread events over N days')

    def handle(self, *args, **options):
        num_events = options['events']
        num_days = options['days']

        ab_test, _ = ABTest.objects.get_or_create(
            slug='modal_test',
            defaults={'name': 'Modal Test', 'is_active': True},
        )

        now = timezone.now()
        sessions = [uuid.uuid4().hex[:16] for _ in range(num_events // 5)]
        variants = ['A', 'B']

        events = []
        for _ in range(num_events):
            session = random.choice(sessions)
            variant = random.choice(variants)
            action = random.choice(ACTIONS)
            day_offset = random.randint(0, num_days)
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            created = now - timedelta(days=day_offset, hours=hour, minutes=minute)
            device = random.choice(DEVICE_TYPES)
            browser = random.choice(BROWSERS)
            os_name = random.choice(OS_LIST)

            events.append(ABEvent(
                test=ab_test,
                variant=variant,
                action=action,
                session_key=session,
                created_at=created,
                meta={
                    'device_type': device,
                    'browser': browser,
                    'os': os_name,
                    'screen_width': random.choice([1920, 1440, 1366, 375, 414, 768]),
                    'screen_height': random.choice([1080, 900, 768, 667, 896, 1024]),
                },
            ))

        ABEvent.objects.bulk_create(events)

        # auto_now_add overrides created_at on bulk_create, so update via raw SQL
        created_events = ABEvent.objects.filter(test=ab_test).order_by('-id')[:num_events]
        for i, event in enumerate(created_events):
            target_date = events[i].created_at
            ABEvent.objects.filter(pk=event.pk).update(created_at=target_date)

        self.stdout.write(self.style.SUCCESS(
            f'Created {num_events} events for test "{ab_test.name}" over {num_days} days'
        ))
