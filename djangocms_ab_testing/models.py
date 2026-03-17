from django.db import models
from django.db.models import F
from cms.models import CMSPlugin


class ABTest(models.Model):
    """A standalone A/B test definition."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AB Test"
        verbose_name_plural = "AB Tests"
        ordering = ["-created_at"]

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.name} ({status})"


class ABTestPluginModel(CMSPlugin):
    """Container plugin for an A/B test. Children are ABTestVariantPlugin instances."""
    test = models.ForeignKey(
        ABTest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="AB Test",
    )
    is_active = models.BooleanField(default=True)
    forced_variant = models.CharField(
        max_length=2,
        blank=True,
        default="",
        verbose_name="Force variant (debug)",
        help_text="Leave empty for normal rotation. Set a variant key (e.g. 'A' or 'B') to always show that variant.",
    )

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        name = self.test.slug if self.test else "unlinked"
        return f"AB Test: {name} ({status})"


class ABTestVariantPluginModel(CMSPlugin):
    """A single variant. Children are the variant's CMS content."""
    variant_name = models.CharField(max_length=100)
    variant_key = models.CharField(max_length=2)

    def __str__(self):
        return f"Variant {self.variant_key}: {self.variant_name}"


class ABCounter(models.Model):
    """Atomic counter for round-robin variant assignment."""
    test = models.OneToOneField(
        ABTest,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="counter",
    )
    test_name = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "AB Counter"
        verbose_name_plural = "AB Counters"

    def __str__(self):
        return f"{self.test_name} (count: {self.count})"

    @classmethod
    def next_variant(cls, test_slug, variant_keys):
        """Atomic increment, returns the next variant key via round-robin."""
        counter, _ = cls.objects.get_or_create(test_name=test_slug)
        cls.objects.filter(pk=counter.pk).update(count=F('count') + 1)
        counter.refresh_from_db()
        index = (counter.count - 1) % len(variant_keys)
        return variant_keys[index]


class ABEvent(models.Model):
    """Tracked user interaction."""
    test = models.ForeignKey(
        ABTest,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="events",
    )
    variant = models.CharField(max_length=2)
    action = models.CharField(max_length=20)
    session_key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "AB Event"
        verbose_name_plural = "AB Events"
        indexes = [
            models.Index(fields=["test", "action", "created_at"]),
            models.Index(fields=["test", "variant"]),
        ]

    def __str__(self):
        return f"{self.variant} - {self.action} ({self.created_at})"
