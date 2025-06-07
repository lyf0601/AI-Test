"""
信号处理器
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out

from .models import UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    用户创建时自动创建用户资料
    """
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"为用户 {instance.username} 创建了用户资料")
        except Exception as e:
            logger.error(f"创建用户资料失败: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    用户保存时保存用户资料
    """
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except UserProfile.DoesNotExist:
        # 如果用户资料不存在，创建一个
        UserProfile.objects.create(user=instance)


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    用户登录信号处理
    """
    logger.info(f"用户登录信号: {user.username} from {request.META.get('REMOTE_ADDR', 'unknown')}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    用户注销信号处理
    """
    if user:
        logger.info(f"用户注销信号: {user.username}")
    else:
        logger.info("匿名用户注销") 