"""
账户应用 URL 配置
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'accounts'

urlpatterns = [
    # 用户认证相关
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.UserLogoutView.as_view(), name='user-logout'),
    path('refresh/', views.refresh_token_view, name='token-refresh'),
    
    # 用户信息相关
    path('me/', views.UserInfoView.as_view(), name='user-info'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # 用户统计和记录
    path('dashboard/', views.dashboard_stats_view, name='dashboard-stats'),
    path('login-records/', views.LoginRecordListView.as_view(), name='login-records'),
    
    # 账户管理
    path('deactivate/', views.deactivate_account_view, name='deactivate-account'),
] 