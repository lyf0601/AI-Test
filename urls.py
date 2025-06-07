"""
主项目 URL 配置
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API 文档
    path('docs/', include_docs_urls(title='DRF Login API')),
    
    # 认证相关 API
    path('api/auth/', include('accounts.urls')),
    
    # API 根路径
    path('api/', include('accounts.urls')),
]

# 在开发环境中提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 设置 Admin 标题
admin.site.site_header = "DRF 登录系统管理"
admin.site.site_title = "DRF 管理"
admin.site.index_title = "欢迎使用 DRF 登录系统" 