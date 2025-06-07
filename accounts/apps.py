"""
Accounts 应用配置
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = '用户账户'
    
    def ready(self):
        """应用准备完成后的初始化"""
        import accounts.signals 