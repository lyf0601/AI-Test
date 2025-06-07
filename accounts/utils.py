"""
工具函数
"""

import re
from django.core.mail import send_mail
from django.conf import settings


def get_client_ip(request):
    """
    获取客户端IP地址
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    获取用户代理信息
    """
    return request.META.get('HTTP_USER_AGENT', '')


def validate_phone_number(phone):
    """
    验证手机号格式
    """
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None


def send_verification_email(user, verification_code):
    """
    发送验证邮件
    """
    subject = '账户验证'
    message = f'''
    您好 {user.username}，
    
    感谢您注册我们的服务！
    
    您的验证码是：{verification_code}
    
    请在注册页面输入此验证码完成账户验证。
    
    如果您没有注册我们的服务，请忽略此邮件。
    
    此邮件由系统自动发送，请勿回复。
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False


def send_password_reset_email(user, reset_link):
    """
    发送密码重置邮件
    """
    subject = '密码重置'
    message = f'''
    您好 {user.username}，
    
    我们收到了您的密码重置请求。
    
    请点击下面的链接重置您的密码：
    {reset_link}
    
    如果您没有请求重置密码，请忽略此邮件。
    
    此链接将在24小时后失效。
    
    此邮件由系统自动发送，请勿回复。
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False


def generate_username_from_email(email):
    """
    从邮箱生成用户名
    """
    username = email.split('@')[0]
    # 移除特殊字符，只保留字母数字下划线
    username = re.sub(r'[^\w]', '', username)
    return username


def format_file_size(size_bytes):
    """
    格式化文件大小
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def is_valid_image_extension(filename):
    """
    验证图片文件扩展名
    """
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    extension = filename.lower().split('.')[-1]
    return f'.{extension}' in valid_extensions 