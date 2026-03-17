from django.conf import settings

DEFAULT_ACTIONS = {"view", "opened", "closed", "requested"}


def get_valid_actions():
    return set(getattr(settings, "AB_TESTING_VALID_ACTIONS", DEFAULT_ACTIONS))
