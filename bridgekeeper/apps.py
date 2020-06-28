from django.apps import AppConfig


class BridgekeeperConfig(AppConfig):
    name = "bridgekeeper"

    def ready(self):
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("permissions")
