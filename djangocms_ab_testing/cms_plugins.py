from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext_lazy as _

from djangocms_ab_testing.models import ABTestPluginModel, ABTestVariantPluginModel
from djangocms_ab_testing.ab_utils import get_ab_variant


@plugin_pool.register_plugin
class ABTestPlugin(CMSPluginBase):
    model = ABTestPluginModel
    name = _("A/B Test Container")
    module = _("A/B Testing")
    render_template = "ab_testing/ab_test_plugin.html"
    allow_children = True
    child_classes = ["ABTestVariantPlugin"]
    cache = False

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        request = context["request"]

        variants = instance.child_plugin_instances or []

        test_slug = instance.test.slug if instance.test else "unknown"

        if not instance.is_active:
            context["active_variant"] = variants[0] if variants else None
            context["ab_test_active"] = False
            return context

        variant_keys = [v.variant_key for v in variants if hasattr(v, 'variant_key')]
        if not variant_keys:
            context["active_variant"] = variants[0] if variants else None
            context["ab_test_active"] = False
            return context

        if instance.forced_variant and instance.forced_variant in variant_keys:
            variant_key = instance.forced_variant
        else:
            variant_key = get_ab_variant(request, test_slug, tuple(variant_keys))

        active_variant = None
        for v in variants:
            if hasattr(v, 'variant_key') and v.variant_key == variant_key:
                active_variant = v
                break

        context["active_variant"] = active_variant
        context["ab_test_active"] = True
        context["variant_key"] = variant_key
        context["test_name"] = test_slug
        return context


@plugin_pool.register_plugin
class ABTestVariantPlugin(CMSPluginBase):
    model = ABTestVariantPluginModel
    name = _("A/B Test Variant")
    module = _("A/B Testing")
    render_template = "ab_testing/ab_test_variant_plugin.html"
    allow_children = True
    require_parent = True
    parent_classes = ["ABTestPlugin"]
