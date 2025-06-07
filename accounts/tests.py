"""
用户认证系统测试
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile, LoginRecord


class UserModelTest(TestCase):
    """用户模型测试"""
    
    def setUp(self):
        """测试准备"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_creation(self):
        """测试用户资料自动创建"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
    
    def test_user_profile_str(self):
        """测试用户资料字符串表示"""
        expected = f"{self.user.username}的资料"
        self.assertEqual(str(self.user.profile), expected)


class UserRegistrationAPITest(APITestCase):
    """用户注册API测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        self.register_url = reverse('accounts:user-register')
    
    def test_user_registration_success(self):
        """测试用户注册成功"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': '新',
            'last_name': '用户'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['message'], '注册成功')
        
        # 验证用户已创建
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_user_registration_password_mismatch(self):
        """测试密码不匹配"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'wrongpass123'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_user_registration_duplicate_username(self):
        """测试用户名重复"""
        # 先创建一个用户
        User.objects.create_user(username='existuser', email='exist@example.com')
        
        data = {
            'username': 'existuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class UserLoginAPITest(APITestCase):
    """用户登录API测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        self.login_url = reverse('accounts:user-login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_login_success_with_username(self):
        """测试使用用户名登录成功"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['message'], '登录成功')
    
    def test_user_login_success_with_email(self):
        """测试使用邮箱登录成功"""
        data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '登录成功')
    
    def test_user_login_wrong_password(self):
        """测试密码错误"""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '登录失败')
    
    def test_user_login_nonexistent_user(self):
        """测试用户不存在"""
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '登录失败')


class UserProfileAPITest(APITestCase):
    """用户资料API测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile_url = reverse('accounts:user-profile')
        
        # 获取token并设置认证
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_user_profile(self):
        """测试获取用户资料"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_update_user_profile(self):
        """测试更新用户资料"""
        data = {
            'phone': '13800138000',
            'bio': '这是我的个人简介',
            'location': '北京'
        }
        response = self.client.patch(self.profile_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '资料更新成功')
        
        # 验证更新结果
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone, '13800138000')
        self.assertEqual(self.user.profile.bio, '这是我的个人简介')


class LoginRecordTest(TestCase):
    """登录记录测试"""
    
    def setUp(self):
        """测试准备"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_record_creation(self):
        """测试登录记录创建"""
        record = LoginRecord.objects.create(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            is_successful=True
        )
        
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.ip_address, '127.0.0.1')
        self.assertTrue(record.is_successful)
    
    def test_login_record_str(self):
        """测试登录记录字符串表示"""
        record = LoginRecord.objects.create(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            is_successful=True
        )
        
        expected = f"{self.user.username} - {record.login_time.strftime('%Y-%m-%d %H:%M:%S')} - 成功"
        self.assertEqual(str(record), expected)


class JWTTokenTest(APITestCase):
    """JWT Token测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.refresh_url = reverse('accounts:token-refresh')
    
    def test_token_refresh(self):
        """测试token刷新"""
        refresh = RefreshToken.for_user(self.user)
        
        data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_invalid(self):
        """测试无效token刷新"""
        data = {'refresh': 'invalid_token'}3131313
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data) 