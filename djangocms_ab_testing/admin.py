import json
from collections import Counter
from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from import_export import resources
from import_export.admin import ExportMixin

from djangocms_ab_testing.conf import get_valid_actions
from djangocms_ab_testing.models import ABCounter, ABEvent, ABTest


class ABEventResource(resources.ModelResource):
    class Meta:
        model = ABEvent
        fields = ('id', 'variant', 'action', 'session_key', 'created_at', 'meta')


@admin.register(ABEvent)
class ABEventAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('variant', 'action', 'session_key', 'created_at', 'test')
    list_filter = ('test', 'variant', 'action', 'created_at')
    search_fields = ('session_key',)
    readonly_fields = ('variant', 'action', 'session_key', 'created_at', 'meta', 'test')
    resource_class = ABEventResource

    def has_module_permission(self, request):
        return False


@admin.register(ABCounter)
class ABCounterAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'count', 'test')
    readonly_fields = ('test_name', 'count', 'test')

    def has_module_permission(self, request):
        return False


@admin.register(ABTest)
class ABTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'event_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('name',),
        }),
        ('Settings', {
            'classes': ('collapse',),
            'fields': ('slug', 'is_active', 'description', 'created_at'),
        }),
    )

    change_form_template = "ab_testing/admin/abtest_change_form.html"

    def event_count(self, obj):
        return obj.events.count()
    event_count.short_description = "Events"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/dashboard-data/',
                self.admin_site.admin_view(self.dashboard_data_view),
                name='ab_testing_abtest_dashboard_data',
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            ab_test = ABTest.objects.filter(pk=object_id).first()
            if ab_test:
                stats = self._compute_stats(ab_test)
                extra_context['initial_stats'] = json.dumps(stats)
                extra_context['dashboard_data_url'] = reverse(
                    'admin:ab_testing_abtest_dashboard_data', args=[object_id]
                )
                extra_context['has_dashboard'] = True
                counter = ABCounter.objects.filter(test=ab_test).first()
                extra_context['counter_value'] = counter.count if counter else 0
        return super().change_view(request, object_id, form_url, extra_context)

    def dashboard_data_view(self, request, pk):
        ab_test = ABTest.objects.filter(pk=pk).first()
        if not ab_test:
            return JsonResponse({'error': 'Not found'}, status=404)

        filters = {}
        for key in ('date_from', 'date_to', 'device_type', 'browser', 'os', 'screen_size'):
            val = request.GET.get(key)
            if val:
                filters[key] = val

        stats = self._compute_stats(ab_test, **filters)
        return JsonResponse(stats)

    def _compute_stats(self, ab_test, date_from=None, date_to=None,
                       device_type=None, browser=None, os=None, screen_size=None):
        qs = ABEvent.objects.filter(test=ab_test)

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if device_type:
            qs = qs.filter(meta__device_type=device_type)
        if browser:
            qs = qs.filter(meta__browser=browser)
        if os:
            qs = qs.filter(meta__os=os)
        if screen_size:
            w, h = screen_size.split('x')
            qs = qs.filter(meta__screen_width=int(w), meta__screen_height=int(h))

        # Per-variant stats
        variants = list(qs.values_list('variant', flat=True).distinct().order_by('variant'))
        variant_stats = []
        for variant in variants:
            vqs = qs.filter(variant=variant)
            unique_sessions = vqs.values('session_key').distinct().count()
            valid_actions = get_valid_actions()
            action_counts = {}
            for action_name in valid_actions:
                action_counts[action_name] = vqs.filter(action=action_name).count()
            opens = action_counts.get('opened', 0)
            requests = action_counts.get('requested', 0)
            conv_rate = round(requests / opens * 100, 1) if opens > 0 else 0
            stat = {
                'variant': variant,
                'unique_sessions': unique_sessions,
                'conversion_rate': conv_rate,
            }
            stat.update(action_counts)
            variant_stats.append(stat)

        # Daily time-series for opens per variant
        daily_data = {}
        for variant in variants:
            vqs = qs.filter(variant=variant, action='opened')
            daily = (
                vqs.annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(count=Count('id'))
                .order_by('day')
            )
            for entry in daily:
                day_str = str(entry['day'])
                if day_str not in daily_data:
                    daily_data[day_str] = {}
                daily_data[day_str][variant] = entry['count']

        sorted_days = sorted(daily_data.keys())
        timeseries = {
            'labels': sorted_days,
            'datasets': {},
        }
        for v in variants:
            timeseries['datasets'][v] = [daily_data.get(d, {}).get(v, 0) for d in sorted_days]

        # Daily conversion rate time-series per variant
        conv_daily = {}
        for variant in variants:
            vqs = qs.filter(variant=variant)
            opens_by_day = dict(
                vqs.filter(action='opened')
                .annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(count=Count('id'))
                .order_by('day')
                .values_list('day', 'count')
            )
            reqs_by_day = dict(
                vqs.filter(action='requested')
                .annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(count=Count('id'))
                .order_by('day')
                .values_list('day', 'count')
            )
            all_days = set(opens_by_day.keys()) | set(reqs_by_day.keys())
            for d in all_days:
                day_str = str(d)
                if day_str not in conv_daily:
                    conv_daily[day_str] = {}
                o = opens_by_day.get(d, 0)
                r = reqs_by_day.get(d, 0)
                conv_daily[day_str][variant] = round(r / o * 100, 1) if o > 0 else 0

        sorted_conv_days = sorted(conv_daily.keys())
        conv_timeseries = {
            'labels': sorted_conv_days,
            'datasets': {},
        }
        for v in variants:
            conv_timeseries['datasets'][v] = [conv_daily.get(d, {}).get(v, 0) for d in sorted_conv_days]

        # Distribution charts: per-variant breakdown by device, browser, os, screen_size
        distributions = self._compute_distributions(qs, variants)

        # Filter options (from unfiltered data for this test)
        all_events = ABEvent.objects.filter(test=ab_test)
        device_types = set()
        browsers = set()
        os_list = set()
        screen_sizes = set()
        for meta in all_events.values_list('meta', flat=True).iterator():
            if not meta:
                continue
            if meta.get('device_type'):
                device_types.add(meta['device_type'])
            if meta.get('browser'):
                browsers.add(meta['browser'])
            if meta.get('os'):
                os_list.add(meta['os'])
            sw = meta.get('screen_width')
            sh = meta.get('screen_height')
            if sw and sh:
                screen_sizes.add(f"{sw}x{sh}")

        return {
            'total_events': qs.count(),
            'total_sessions': qs.values('session_key').distinct().count(),
            'variant_stats': variant_stats,
            'timeseries': timeseries,
            'conv_timeseries': conv_timeseries,
            'distributions': distributions,
            'filter_options': {
                'device_types': sorted(device_types),
                'browsers': sorted(browsers),
                'os_list': sorted(os_list),
                'screen_sizes': sorted(screen_sizes),
            },
        }

    def _compute_distributions(self, qs, variants):
        """Compute per-variant distributions for device, browser, os, screen_size."""
        result = {}
        for dim_key, meta_keys in [
            ('device', ['device_type']),
            ('browser', ['browser']),
            ('os', ['os']),
            ('screen_size', ['screen_width', 'screen_height']),
        ]:
            # Collect all labels and per-variant counts
            variant_counters = {}
            all_labels = set()
            for variant in variants:
                counter = Counter()
                for meta in qs.filter(variant=variant).values_list('meta', flat=True).iterator():
                    if not meta:
                        continue
                    if dim_key == 'screen_size':
                        sw = meta.get('screen_width')
                        sh = meta.get('screen_height')
                        if sw and sh:
                            label = f"{sw}x{sh}"
                            counter[label] += 1
                            all_labels.add(label)
                    else:
                        val = meta.get(meta_keys[0])
                        if val:
                            counter[val] += 1
                            all_labels.add(val)
                variant_counters[variant] = counter

            sorted_labels = sorted(all_labels)
            datasets = {}
            for variant in variants:
                datasets[variant] = [variant_counters[variant].get(l, 0) for l in sorted_labels]

            result[dim_key] = {
                'labels': sorted_labels,
                'datasets': datasets,
            }
        return result
