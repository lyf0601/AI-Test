"""
用户相关模型
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """
    用户扩展信息模型
    如果不需要自定义用户模型，可以使用这个模型来扩展用户信息
    """
    user = models.OneToOneField(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='用户'
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True, 
        verbose_name='头像'
    )
    phone = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        verbose_name='手机号'
    )
    birth_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='生日'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name='个人简介'
    )
    location = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='所在地'
    )
    website = models.URLField(
        blank=True, 
        verbose_name='个人网站'
    )
    gender_choices = [
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
    ]
    gender = models.CharField(
        max_length=1, 
        choices=gender_choices, 
        null=True, 
        blank=True,
        verbose_name='性别'
    )
    is_verified = models.BooleanField(
        default=False, 
        verbose_name='是否已验证'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='更新时间'
    )

    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}的资料"

    @property
    def age(self):
        """计算年龄"""
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    def get_full_name(self):
        """获取完整姓名"""
        return self.user.get_full_name() or self.user.username


class LoginRecord(models.Model):
    """
    登录记录模型
    """
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='login_records',
        verbose_name='用户'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='IP地址'
    )
    user_agent = models.TextField(
        verbose_name='用户代理',
        blank=True
    )
    login_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='登录时间'
    )
    login_method = models.CharField(
        max_length=20,
        choices=[
            ('password', '密码登录'),
            ('social', '社交登录'),
            ('sms', '短信登录'),
        ],
        default='password',
        verbose_name='登录方式'
    )
    is_successful = models.BooleanField(
        default=True,
        verbose_name='是否成功'
    )
    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='失败原因'
    )

    class Meta:
        db_table = 'login_record'
        verbose_name = '登录记录'
        verbose_name_plural = '登录记录'
        ordering = ['-login_time']

    def __str__(self):
        status = "成功" if self.is_successful else "失败"
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')} - {status}"


# 如果需要完全自定义用户模型，可以使用下面的代码
# 需要在 settings.py 中设置 AUTH_USER_MODEL = 'accounts.User'

# class User(AbstractUser):
#     """
#     自定义用户模型
#     """
#     email = models.EmailField(
#         verbose_name='邮箱',
#         unique=True,
#         help_text='用户邮箱地址'
#     )
#     phone = models.CharField(
#         max_length=20,
#         null=True,
#         blank=True,
#         verbose_name='手机号'
#     )
#     avatar = models.ImageField(
#         upload_to='avatars/',
#         null=True,
#         blank=True,
#         verbose_name='头像'
#     )
#     is_verified = models.BooleanField(
#         default=False,
#         verbose_name='是否已验证'
#     )
#     
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username']
#     
#     class Meta:
#         db_table = 'custom_user'
#         verbose_name = '用户'
#         verbose_name_plural = '用户' 