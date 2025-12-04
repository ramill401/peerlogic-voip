from django.apps import AppConfig


class VoipAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.voip_admin'
    verbose_name = 'VoIP Administration'
