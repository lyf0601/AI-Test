"""
用户认证相关序列化器
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re

from .models import UserProfile, LoginRecord


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    """
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password'},
        help_text='密码长度至少8位'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='确认密码'
    )
    email = serializers.EmailField(
        required=True,
        help_text='邮箱地址'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')

    def validate_username(self, value):
        """验证用户名"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        
        # 用户名只能包含字母、数字和下划线
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("用户名只能包含字母、数字和下划线")
        
        return value

    def validate_email(self, value):
        """验证邮箱"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("邮箱已被注册")
        return value

    def validate_password(self, value):
        """验证密码强度"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """验证密码确认"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': '两次密码输入不一致'
            })
        return attrs

    def create(self, validated_data):
        """创建用户"""
        # 移除确认密码字段
        validated_data.pop('password_confirm')
        
        # 创建用户
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # 创建用户扩展信息
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    用户登录序列化器
    """
    username = serializers.CharField(
        max_length=150,
        help_text='用户名或邮箱'
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='密码'
    )

    def validate(self, attrs):
        """验证登录信息"""
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # 尝试使用用户名登录
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            # 如果用户名登录失败，尝试使用邮箱登录
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(
                        request=self.context.get('request'),
                        username=user_obj.username,
                        password=password
                    )
                except User.DoesNotExist:
                    pass

            if not user:
                msg = '用户名/邮箱或密码错误'
                raise serializers.ValidationError(msg, code='authorization')

            if not user.is_active:
                msg = '用户账户已被禁用'
                raise serializers.ValidationError(msg, code='authorization')

            attrs['user'] = user
            return attrs
        else:
            msg = '必须提供用户名和密码'
            raise serializers.ValidationError(msg, code='authorization')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户资料序列化器
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    age = serializers.ReadOnlyField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'avatar', 'phone', 'birth_date', 'bio', 'location', 
            'website', 'gender', 'is_verified', 'age', 'full_name',
            'created_at', 'updated_at', 'date_joined', 'last_login'
        )
        read_only_fields = ('is_verified', 'created_at', 'updated_at')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    用户资料更新序列化器
    """
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)

    class Meta:
        model = UserProfile
        fields = (
            'avatar', 'phone', 'birth_date', 'bio', 'location', 
            'website', 'gender', 'first_name', 'last_name'
        )

    def update(self, instance, validated_data):
        """更新用户资料"""
        # 处理用户基本信息
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # 处理用户扩展信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    修改密码序列化器
    """
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='当前密码'
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='新密码'
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='确认新密码'
    )

    def validate_old_password(self, value):
        """验证当前密码"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('当前密码错误')
        return value

    def validate_new_password(self, value):
        """验证新密码强度"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """验证新密码确认"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': '两次新密码输入不一致'
            })
        return attrs

    def save(self, **kwargs):
        """保存新密码"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginRecordSerializer(serializers.ModelSerializer):
    """
    登录记录序列化器
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LoginRecord
        fields = (
            'id', 'username', 'ip_address', 'user_agent', 
            'login_time', 'login_method', 'is_successful', 'failure_reason'
        )
        read_only_fields = ('id', 'username', 'login_time')


class UserSimpleSerializer(serializers.ModelSerializer):
    """
    用户简单信息序列化器
    """
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'date_joined', 'last_login', 'profile')
        read_only_fields = ('id', 'username', 'email', 'date_joined', 'last_login') 