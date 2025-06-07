"""
Django Admin 配置
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import UserProfile, LoginRecord


class UserProfileInline(admin.StackedInline):
    """用户资料内联编辑"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户资料'
    extra = 0
    
    fieldsets = (
        ('基本信息', {
            'fields': ('avatar', 'phone', 'birth_date', 'gender')
        }),
        ('详细信息', {
            'fields': ('bio', 'location', 'website')
        }),
        ('状态', {
            'fields': ('is_verified',)
        }),
    )


class CustomUserAdmin(BaseUserAdmin):
    """自定义用户管理"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 
                   'is_active', 'is_staff', 'date_joined', 'has_profile')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    def has_profile(self, obj):
        """检查是否有用户资料"""
        try:
            return obj.profile is not None
        except UserProfile.DoesNotExist:
            return False
    has_profile.boolean = True
    has_profile.short_description = '有资料'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料管理"""
    list_display = ('user', 'phone', 'gender', 'is_verified', 'created_at')
    list_filter = ('gender', 'is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'age_display')
    
    fieldsets = (
        ('关联用户', {
            'fields': ('user',)
        }),
        ('基本信息', {
            'fields': ('avatar', 'phone', 'birth_date', 'gender', 'age_display')
        }),
        ('详细信息', {
            'fields': ('bio', 'location', 'website')
        }),
        ('状态信息', {
            'fields': ('is_verified', 'created_at', 'updated_at')
        }),
    )
    
    def age_display(self, obj):
        """显示年龄"""
        age = obj.age
        return f"{age}岁" if age else "未知"
    age_display.short_description = '年龄'


@admin.register(LoginRecord)
class LoginRecordAdmin(admin.ModelAdmin):
    """登录记录管理"""
    list_display = ('user', 'ip_address', 'login_method', 'is_successful', 
                   'login_time', 'user_agent_short')
    list_filter = ('login_method', 'is_successful', 'login_time')
    search_fields = ('user__username', 'ip_address', 'user_agent')
    readonly_fields = ('login_time',)
    date_hierarchy = 'login_time'
    ordering = ('-login_time',)
    
    fieldsets = (
        ('用户信息', {
            'fields': ('user', 'login_time')
        }),
        ('登录详情', {
            'fields': ('ip_address', 'login_method', 'is_successful', 'failure_reason')
        }),
        ('技术信息', {
            'fields': ('user_agent',),
            'classes': ('collapse',)
        }),
    )
    
    def user_agent_short(self, obj):
        """显示简短的用户代理信息"""
        if obj.user_agent:
            return obj.user_agent[:50] + "..." if len(obj.user_agent) > 50 else obj.user_agent
        return "-"
    user_agent_short.short_description = '用户代理'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('user')


# 重新注册User模型以使用自定义的UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# 自定义Admin站点标题
admin.site.site_header = "DRF 登录系统管理后台"
admin.site.site_title = "DRF 管理"
admin.site.index_title = "欢迎使用 DRF 登录系统管理后台" 