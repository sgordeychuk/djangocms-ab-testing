from django.urls import path

from djangocms_ab_testing.views import ab_event_view

urlpatterns = [
    path("ab-event/", ab_event_view, name="ab_event"),
]
