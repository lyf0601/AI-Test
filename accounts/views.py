"""
用户认证相关视图
"""

import logging
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db import transaction
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import UserProfile, LoginRecord
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    LoginRecordSerializer,
    UserSimpleSerializer
)
from .utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)


class UserRegistrationView(generics.CreateAPIView):
    """
    用户注册视图
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """创建用户"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # 记录注册日志
            logger.info(f"用户注册成功: {user.username} ({user.email})")
            
            # 生成JWT token
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': '注册成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    用户登录视图
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """用户登录"""
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # 记录登录信息
            self._record_login(request, user, True)
            
            # 更新最后登录时间
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # 生成JWT token
            refresh = RefreshToken.for_user(user)
            
            # 获取用户资料
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                # 如果用户没有资料，创建一个
                profile = UserProfile.objects.create(user=user)
            
            logger.info(f"用户登录成功: {user.username}")
            
            return Response({
                'message': '登录成功',
                'user': UserSimpleSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        else:
            # 记录登录失败
            username = request.data.get('username', '')
            self._record_login(request, None, False, '登录信息验证失败')
            
            logger.warning(f"用户登录失败: {username} - {serializer.errors}")
            
            return Response({
                'message': '登录失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def _record_login(self, request, user, is_successful, failure_reason=''):
        """记录登录信息"""
        try:
            LoginRecord.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                login_method='password',
                is_successful=is_successful,
                failure_reason=failure_reason
            )
        except Exception as e:
            logger.error(f"记录登录信息失败: {e}")


class UserLogoutView(APIView):
    """
    用户注销视图
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """用户注销"""
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logger.info(f"用户注销: {request.user.username}")
            
            return Response({
                'message': '注销成功'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"用户注销失败: {e}")
            return Response({
                'message': '注销失败',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    用户资料视图
    GET /api/auth/profile/ - 获取用户资料
    PUT/PATCH /api/auth/profile/ - 更新用户资料
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """获取当前用户的资料"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_serializer_class(self):
        """根据请求方法返回不同的序列化器"""
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def update(self, request, *args, **kwargs):
        """更新用户资料"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            self.perform_update(serializer)
            
        logger.info(f"用户资料更新: {request.user.username}")
        
        return Response({
            'message': '资料更新成功',
            'data': UserProfileSerializer(instance).data
        })


class ChangePasswordView(APIView):
    """
    修改密码视图
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            
            logger.info(f"用户修改密码: {request.user.username}")
            
            return Response({
                'message': '密码修改成功'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': '密码修改失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserInfoView(generics.RetrieveAPIView):
    """
    获取当前用户信息视图
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSimpleSerializer

    def get_object(self):
        """返回当前登录用户"""
        return self.request.user


class LoginRecordListView(generics.ListAPIView):
    """
    用户登录记录列表视图
    GET /api/auth/login-records/
    """
    serializer_class = LoginRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取当前用户的登录记录"""
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 30
        
        start_date = timezone.now() - timedelta(days=days)
        
        return LoginRecord.objects.filter(
            user=self.request.user,
            login_time__gte=start_date
        ).order_by('-login_time')


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    刷新token视图
    POST /api/auth/refresh/
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'error': '需要提供refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken(refresh_token)
        
        return Response({
            'access': str(refresh.access_token)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Token无效或已过期'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """
    用户仪表板统计信息
    GET /api/auth/dashboard/
    """
    user = request.user
    
    # 获取用户统计信息
    login_records = LoginRecord.objects.filter(user=user)
    recent_logins = login_records.filter(
        login_time__gte=timezone.now() - timedelta(days=30)
    )
    
    stats = {
        'user_info': {
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'is_active': user.is_active,
        },
        'login_stats': {
            'total_logins': login_records.count(),
            'recent_logins': recent_logins.count(),
            'successful_logins': login_records.filter(is_successful=True).count(),
            'failed_logins': login_records.filter(is_successful=False).count(),
        }
    }
    
    # 获取用户资料
    try:
        profile = user.profile
        stats['profile'] = UserProfileSerializer(profile).data
    except UserProfile.DoesNotExist:
        stats['profile'] = None
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_account_view(request):
    """
    停用账户视图
    POST /api/auth/deactivate/
    """
    password = request.data.get('password')
    if not password:
        return Response({
            'error': '需要提供密码确认'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    if not user.check_password(password):
        return Response({
            'error': '密码错误'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 停用用户账户
    user.is_active = False
    user.save()
    
    logger.info(f"用户停用账户: {user.username}")
    
    return Response({
        'message': '账户已停用'
    }, status=status.HTTP_200_OK) 