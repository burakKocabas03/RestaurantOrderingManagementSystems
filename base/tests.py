from django.test import TestCase, Client
from django.urls import reverse
from .models import Users, Table, Order, Orderitem, Menuitem, Category, Cart, Cartitem
from django.utils import timezone
from django.contrib.auth.models import User as DjangoUser
import json

# Create your tests here.

class RestaurantTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Django User oluştur
        self.django_user = DjangoUser.objects.create_user(username='testuser', password='1234')
        # Kendi Users modelinden de oluştur
        self.user = Users.objects.create(user_id=1, username='testuser', password='1234', fullname='Test User', user_type='waiter', role='waiter')
        self.category = Category.objects.create(category_id=1, category_name='Ana Yemek')
        self.menuitem = Menuitem.objects.create(item_id=1, name='Köfte', price=100, is_avaible=True, category=self.category)
        self.table = Table.objects.create(table_id=1, table_number=1, table_status='available', user=self.user)
        self.cart = Cart.objects.create(table=self.table, is_active=True)

    def test_table_management_page(self):
        # Django User ile login ol
        self.client.login(username='testuser', password='1234')
        response = self.client.get(reverse('table_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Masa Yönetimi')

    def test_order_create_and_delete(self):
        # Sipariş oluştur
        order = Order.objects.create(order_id=1, table=self.table, status='completed', created_at=timezone.now())
        Orderitem.objects.create(order=order, item=self.menuitem, quantity=1, unit_price=100)
        # Silme endpointine istek gönder
        self.client.login(username='testuser', password='1234')
        response = self.client.post(reverse('delete_order', args=[self.table.table_id, order.order_id]), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(order_id=order.order_id).count(), 0)

    def test_user_creation(self):
        user_count = Users.objects.count()
        Users.objects.create(user_id=2, username='another', password='pass', fullname='Another User', user_type='waiter', role='waiter')
        self.assertEqual(Users.objects.count(), user_count + 1)

    # --- UNIT TESTS ---
    def test_menuitem_creation(self):
        """Menü ürünü oluşturma unit testi"""
        item = Menuitem.objects.create(item_id=2, name='Pizza', price=150, is_avaible=True, category=self.category)
        self.assertEqual(item.name, 'Pizza')
        self.assertEqual(item.price, 150)
        self.assertTrue(item.is_avaible)

    def test_add_to_cart_creates_cartitem(self):
        """Sepete ürün ekleme fonksiyonu unit testi"""
        response = self.client.post(
            reverse('add_to_cart', args=[self.table.table_number]),
            data=json.dumps({'item_id': self.menuitem.item_id, 'quantity': 2, 'notes': 'Bol soslu'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Cartitem.objects.filter(cart__table=self.table, item=self.menuitem).exists())

    # --- COMPONENT TESTS ---
    def test_place_order_clears_cart(self):
        """Sipariş oluşturulunca sepetin temizlenmesi component testi"""
        # Sepete ürün ekle (endpoint ile)
        self.client.login(username='testuser', password='1234')
        self.client.post(
            reverse('add_to_cart', args=[self.table.table_number]),
            data=json.dumps({'item_id': self.menuitem.item_id, 'quantity': 1, 'notes': 'Test notu'}),
            content_type='application/json'
        )
        # Sipariş ver
        response = self.client.post(
            reverse('place_order', args=[self.table.table_number]),
            data=json.dumps({'type': 'dine_in'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Sepet tekrar çekilmeli (çünkü sipariş sonrası yeni bir aktif sepet oluşabilir)
        cart = Cart.objects.filter(table=self.table, is_active=True).first()
        if cart:
            self.assertFalse(Cartitem.objects.filter(cart=cart).exists())
        else:
            self.assertTrue(True)  # Hiç aktif sepet yoksa da test başarılı

    def test_table_management_lists_tables(self):
        """Masa yönetim ekranında masaların listelenmesi component testi"""
        self.client.login(username='testuser', password='1234')
        response = self.client.get(reverse('table_management'))
        self.assertContains(response, f'Masa {self.table.table_number}')

    def test_add_to_cart_and_check_cart_status(self):
        """Sepete ürün ekleme ve sepetin durumunu kontrol etme component testi"""
        self.client.login(username='testuser', password='1234')
        # Sepete ürün ekle
        response = self.client.post(
            reverse('add_to_cart', args=[self.table.table_number]),
            data=json.dumps({'item_id': self.menuitem.item_id, 'quantity': 1, 'notes': 'Test notu'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Sepet durumunu kontrol et
        cart = Cart.objects.filter(table=self.table, is_active=True).first()
        self.assertIsNotNone(cart)
        self.assertTrue(Cartitem.objects.filter(cart=cart, item=self.menuitem).exists())

    # --- SYSTEM TESTS ---
    def test_user_can_order_and_pay(self):
        """Kullanıcı sipariş verip ödeme yapabiliyor mu system testi"""
        self.client.login(username='testuser', password='1234')
        # Sepete ürün ekle (endpoint ile)
        self.client.post(
            reverse('add_to_cart', args=[self.table.table_number]),
            data=json.dumps({'item_id': self.menuitem.item_id, 'quantity': 1}),
            content_type='application/json'
        )
        # Sipariş ver
        order_response = self.client.post(
            reverse('place_order', args=[self.table.table_number]),
            data=json.dumps({'type': 'dine_in'}),
            content_type='application/json'
        )
        self.assertEqual(order_response.status_code, 200)
        # Sipariş gerçekten oluştu mu ve status 'received' mi?
        order_id = order_response.json().get('order_id')
        order = Order.objects.get(order_id=order_id)
        self.assertEqual(order.status, 'received')
        # Ödeme ekranına git
        response = self.client.get(reverse('payment', args=[self.table.table_id]))
        self.assertEqual(response.status_code, 200)
        # Ödeme yap
        pay_response = self.client.post(
            reverse('process_payment'),
            data=json.dumps({'order_ids': [order_id], 'payment_method': 'cash', 'amount': 100}),
            content_type='application/json'
        )
        self.assertEqual(pay_response.status_code, 200)
        self.assertIn('success', pay_response.json()['status'])

    def test_table_management_requires_login(self):
        """Giriş yapmadan masa yönetimine erişim engelleniyor mu system testi"""
        self.client.logout()
        response = self.client.get(reverse('table_management'))
        self.assertNotEqual(response.status_code, 200)  # 302 veya 403 beklenir

    def test_user_can_add_to_cart_and_check_status(self):
        """Kullanıcı sepete ürün ekleyip sepetin durumunu kontrol edebiliyor mu sistem testi"""
        self.client.login(username='testuser', password='1234')
        # Sepete ürün ekle
        response = self.client.post(
            reverse('add_to_cart', args=[self.table.table_number]),
            data=json.dumps({'item_id': self.menuitem.item_id, 'quantity': 1, 'notes': 'Test notu'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Sepet durumunu kontrol et
        cart = Cart.objects.filter(table=self.table, is_active=True).first()
        self.assertIsNotNone(cart)
        self.assertTrue(Cartitem.objects.filter(cart=cart, item=self.menuitem).exists())

