from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from .models import Menuitem, Category, Order, Orderitem, Table, Cart, Cartitem, Users, Payment, Staff
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime, timezone
from django.db import models
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone
from django.db import connection
import time
from django.contrib import messages
from django.views.decorators.http import require_POST
from decimal import Decimal
import decimal
from django.db import transaction
from django.contrib.auth.hashers import make_password

def index(request):
    # Ana sayfada masaları göster
    tables = Table.objects.all()
    return render(request, 'index.html', {
        'tables': tables
    })

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        fullname = request.POST.get('fullname')
        phone_number = request.POST.get('phone_number')
        user_type = request.POST.get('user_type', 'customer')
        
        # Kullanıcı adı kontrolü
        if Users.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Bu kullanıcı adı zaten kullanılıyor'})
        
        # Yeni kullanıcı oluştur
        user = Users.objects.create(
            username=username,
            password=password,  # Gerçek uygulamada şifre hash'lenmeli
            fullname=fullname,
            phone_number=phone_number,
            user_type=user_type,
            start_date=timezone.now().date()
        )
        
        # Django auth sistemine de ekle
        django_user = DjangoUser.objects.create_user(
            username=username,
            password=password,
            first_name=fullname
        )
        
        # Eğer personel ise Staff kaydı oluştur
        if user_type in ['waiter', 'manager', 'kitchen']:
            Staff.objects.create(
                user=user,
                user_type=user_type
            )
        
        # Otomatik giriş yap
        login(request, django_user)
        
        # Kullanıcı tipine göre yönlendir
        if user_type == 'waiter':
            return redirect('table_management')
        elif user_type == 'admin':
            return redirect('admin_dashboard')
        else:
            return redirect('menu')
            
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def is_customer(user):
    try:
        custom_user = Users.objects.get(username=user.username)
        return custom_user.user_type == 'customer'
    except Users.DoesNotExist:
        return False

def is_waiter(user):
    try:
        custom_user = Users.objects.get(username=user.username)
        return custom_user.user_type == 'waiter'
    except Users.DoesNotExist:
        return False

def is_admin(user):
    try:
        custom_user = Users.objects.get(username=user.username)
        return custom_user.user_type == 'admin'
    except Users.DoesNotExist:
        return False

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            # Önce kendi Users modelimizden kontrol edelim
            custom_user = Users.objects.get(username=username)
            if custom_user.password == password:  # Gerçek uygulamada hash'lenmiş şifre kullanılmalı
                # Django'nun auth sistemine login
                try:
                    django_user = DjangoUser.objects.get(username=username)
                except DjangoUser.DoesNotExist:
                    # Django user yoksa oluştur
                    django_user = DjangoUser.objects.create_user(
                        username=username,
                        password=password,
                        first_name=custom_user.fullname
                    )
                # Staff kaydı varsa ilişkilendir
                try:
                    staff = Staff.objects.get(user=custom_user)
                except Staff.DoesNotExist:
                    if custom_user.user_type in ['waiter', 'manager', 'kitchen']:
                        staff = Staff.objects.create(
                            user=custom_user,
                            user_type=custom_user.user_type
                        )
                login(request, django_user)
                # Admin ise doğrudan admin_dashboard'a yönlendir
                if custom_user.user_type == 'admin' or username == 'admin':
                    return redirect('admin_dashboard')
                # Kullanıcı tipine göre yönlendirme
                if custom_user.user_type == 'waiter':
                    return redirect('table_management')
                else:
                    return redirect('menu')
            else:
                return render(request, 'login.html', {'error': 'Geçersiz şifre'})
        except Users.DoesNotExist:
            return render(request, 'login.html', {'error': 'Kullanıcı bulunamadı'})
    return render(request, 'login.html')

def menu_view(request, table_number=None):
    # Get categories and menu items
    categories = Category.objects.all()
    menu_items = Menuitem.objects.filter(is_avaible=True)
    
    context = {
        'categories': categories,
        'menu_items': menu_items
    }
    
    # If table number is provided, get table-specific information
    if table_number:
        table = get_object_or_404(Table, table_number=table_number)
        cart = Cart.objects.filter(table=table, is_active=True).first()
        active_orders = Order.objects.filter(
            table=table,
            status__in=['received', 'preparing', 'ready']
        )
        context.update({
            'table': table,
            'cart': cart,
            'active_orders': active_orders
        })
    
    return render(request, 'menu.html', context)

def custom_permission_denied_view(request):
    messages.error(request, 'Bu sayfaya erişim yetkiniz yok. Lütfen giriş yapın veya yetkili bir kullanıcı ile tekrar deneyin.')
    return redirect('login')

@login_required
def table_management(request):
    # Kullanıcının staff olup olmadığını kontrol et
    try:
        # Önce Users modelinden kullanıcıyı bul
        users_instance = Users.objects.get(username=request.user.username)
        # Sonra Staff modelinden staff'ı bul
        staff = Staff.objects.get(user=users_instance)
    except (Users.DoesNotExist, Staff.DoesNotExist):
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('permission_denied')
        
    tables = Table.objects.all().order_by('table_number')
    servers = Staff.objects.filter(user_type='waiter')
    
    # Her masa için ilgili siparişleri ve durumlarını ekle
    tables_with_orders = []
    for table in tables:
        orders = Order.objects.filter(table=table).order_by('-created_at')
        
        # Masanın bekleyen nakit ödemesi var mı kontrol et
        pending_payment = None
        if orders.exists():
            pending_payment = Payment.objects.filter(
                order__table=table,
                payment_method='cash',
                status='waiter_approval'
            ).first()
        
        tables_with_orders.append({
            'table': table,
            'orders': orders,
            'pending_payment': pending_payment
        })
    
    return render(request, 'table_management.html', {
        'tables_with_orders': tables_with_orders,
        'servers': servers
    })

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get statistics
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='completed').aggregate(
        total=models.Sum('orderitem__unit_price')
    )['total'] or 0
    
    # Get low stock items
    low_stock_items = Menuitem.objects.filter(
        ingredients__quantity__lt=models.F('ingredients__min_quantity')
    ).distinct()
    
    return render(request, 'admin_dashboard.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'low_stock_items': low_stock_items
    })

@user_passes_test(is_admin)
def manage_menu(request):
    if request.method == 'POST':
        # Handle menu item updates
        item_id = request.POST.get('item_id')
        if item_id:
            item = get_object_or_404(Menuitem, item_id=item_id)
            item.name = request.POST.get('name')
            item.price = request.POST.get('price')
            item.description = request.POST.get('description')
            item.is_avaible = request.POST.get('is_available') == 'on'
            item.save()
        else:
            # Create new item
            Menuitem.objects.create(
                name=request.POST.get('name'),
                price=request.POST.get('price'),
                description=request.POST.get('description'),
                is_avaible=request.POST.get('is_available') == 'on'
            )
        return redirect('manage_menu')
    
    menu_items = Menuitem.objects.all()
    categories = Category.objects.all()
    return render(request, 'manage_menu.html', {
        'menu_items': menu_items,
        'categories': categories
    })

@csrf_exempt
def add_to_cart(request, table_number):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))
            notes = data.get('notes', '')

            # Get table
            table = get_object_or_404(Table, table_number=table_number)

            # Get or create cart for table
            cart, created = Cart.objects.get_or_create(
                table=table,
                is_active=True,
                defaults={'update_date': timezone.now()}
            )

            # Get menu item
            menu_item = get_object_or_404(Menuitem, item_id=item_id)

            # Get default user (you might want to change this based on your requirements)
            default_user = Users.objects.first()

            # Add item to cart
            cart_item, created = Cartitem.objects.get_or_create(
                cart=cart,
                item=menu_item,
                user=default_user,
                defaults={
                    'quantity': quantity,
                    'unit_price': menu_item.price,
                    'notes': notes
                }
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return JsonResponse({
                'status': 'success',
                'message': f'{menu_item.name} sepete eklendi',
                'cart_item': {
                    'name': menu_item.name,
                    'quantity': quantity,
                    'unit_price': float(menu_item.price),
                    'total_price': float(quantity * menu_item.price)
                }
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@csrf_exempt
def place_order(request, table_number):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_type = data.get('type', 'dine_in')
            notes = data.get('notes', '')
            
            # Get table
            table = get_object_or_404(Table, table_number=table_number)
            
            # Get the next order_id from the sequence
            with connection.cursor() as cursor:
                cursor.execute("SELECT nextval('order_order_id_seq')")
                order_id = cursor.fetchone()[0]
            
            # Create order with the generated order_id
            order = Order.objects.create(
                order_id=order_id,
                type=order_type,
                status='received',
                created_at=timezone.now(),
                table=table
            )
            
            # Sepetten ürünleri Orderitem olarak ekle
            cart = Cart.objects.filter(table=table, is_active=True).first()
            if cart:
                cart_items = Cartitem.objects.filter(cart=cart)
                for cart_item in cart_items:
                    quantity = cart_item.quantity if cart_item.quantity is not None else 0
                    unit_price = cart_item.unit_price if cart_item.unit_price is not None else 0
                    order_item, created = Orderitem.objects.get_or_create(
                        order=order,
                        item=cart_item.item,
                        defaults={
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'notes': cart_item.notes
                        }
                    )
                    if not created:
                        order_item.quantity = (order_item.quantity if order_item.quantity is not None else 0) + quantity
                        order_item.save()
            
            # Update table status to occupied
            table.table_status = 'occupied'
            table.save()
            
            # Clear the cart
            if cart:
                cart.is_active = False
                cart.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Sipariş başarıyla oluşturuldu',
                'order_id': order.order_id
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@user_passes_test(is_waiter)
def order_list(request):
    # Tüm aktif siparişleri getir
    orders = Order.objects.filter(
        status__in=['received', 'preparing', 'ready']
    ).order_by('-created_at')
    
    return render(request, 'order_list.html', {
        'orders': orders
    })

@user_passes_test(is_waiter)
def order_detail(request, order_id):
    # Sipariş detaylarını getir
    order = get_object_or_404(Order, order_id=order_id)
    order_items = Orderitem.objects.filter(order=order)
    
    return render(request, 'order_detail.html', {
        'order': order,
        'order_items': order_items
    })

@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status')

            print("Gelen order_id:", order_id)
            print("Gelen new_status:", new_status)

            if new_status not in ['received', 'preparing', 'ready', 'completed']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Geçersiz sipariş durumu'
                }, status=400)

            order = get_object_or_404(Order, order_id=order_id)
            order.status = new_status
            order.save()

            # Eğer sipariş tamamlandıysa, masa durumunu güncelle
            if new_status == 'completed':
                table = order.table
                table.table_status = 'available'
                table.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Sipariş durumu güncellendi'
            })

        except Exception as e:
            print("HATA:", e)  # Konsolda hatayı göreceksin
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@login_required
def kitchen_display(request):
    # Sadece received ve preparing durumundaki siparişleri getir
    orders = Order.objects.filter(
        status__in=['received', 'preparing']
    ).select_related(
        'table'
    ).prefetch_related(
        'orderitem_set',
        'orderitem_set__item'
    ).order_by('-created_at')
    # Her sipariş için orderitem_set'i yükle
    for order in orders:
        order.orderitem_set.all()
    context = {
        'orders': orders,
    }
    return render(request, 'kitchen_display.html', context)

@csrf_exempt
def assign_table(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        table_id = data.get('table_id')
        server_id = data.get('server_id')
        
        Table.objects.filter(table_id=table_id).update(user_id=server_id)
        return JsonResponse({'status': 'success'})

@csrf_exempt
def update_table_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        table_id = data.get('table_id')
        status = data.get('status')
        
        Table.objects.filter(table_id=table_id).update(table_status=status)
        return JsonResponse({'status': 'success'})

def payment_view(request, table_id):
    table = get_object_or_404(Table, table_id=table_id)
    
    # Masanın ödenmemiş siparişlerini getir
    orders = Order.objects.filter(
        table=table,
        status__in=['received', 'preparing', 'ready']
    ).order_by('-created_at')
    
    # Her sipariş için detayları hesapla
    orders_with_details = []
    for order in orders:
        items = Orderitem.objects.filter(order=order)
        total_amount = sum(item.quantity * item.unit_price for item in items)
        
        orders_with_details.append({
            'order_id': order.order_id,
            'created_at': order.created_at,
            'items': items,
            'total_amount': total_amount
        })
    
    context = {
        'table': table,
        'orders': orders_with_details
    }
    
    return render(request, 'base/payment.html', context)

@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_ids = data.get('order_ids', [])
            payment_method = data.get('payment_method')
            amount = data.get('amount')
            
            if not order_ids:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Lütfen en az bir sipariş seçin'
                }, status=400)
            
            orders = Order.objects.filter(order_id__in=order_ids)
            # Sadece ödenmemiş siparişleri seç
            unpaid_orders = orders.exclude(status='completed')
            if not unpaid_orders.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Seçilen siparişlerin hepsi zaten ödenmiş.'
                }, status=400)
            
            table = unpaid_orders.first().table  # İlk ödenmemiş siparişin masasını al
            
            # Her ödenmemiş sipariş için ödeme kaydı oluştur
            for order in unpaid_orders:
                payment = Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method=payment_method,
                    status='pending'  # Nakit ödemeler için başlangıç durumu
                )
                
                # Nakit ödeme ise garson onayı bekleyecek
                if payment_method == 'cash':
                    payment.status = 'waiter_approval'
                    payment.save()
                    return JsonResponse({
                        'status': 'pending',
                        'message': 'Nakit ödeme garson onayı bekliyor',
                        'payment_id': payment.id
                    })
                else:
                    # Diğer ödeme yöntemleri için direkt tamamlandı
                    payment.status = 'completed'
                    payment.save()
                    
                    # Siparişi tamamlandı olarak işaretle
                    order.status = 'completed'
                    order.save()
            
            # Nakit olmayan ödemeler için masanın durumunu kontrol et
            if payment_method != 'cash':
                remaining_orders = Order.objects.filter(
                    table=table,
                    status__in=['received', 'preparing', 'ready']
                ).exists()
                
                # Eğer tüm siparişler tamamlandıysa masayı boşalt
                if not remaining_orders:
                    table.table_status = 'available'
                    table.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Ödeme başarıyla tamamlandı'
                })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@csrf_exempt
def get_payment_status(request, order_id):
    if request.method == 'GET':
        try:
            order = get_object_or_404(Order, order_id=order_id)
            payment = Payment.objects.filter(order=order).first()
            
            if payment:
                return JsonResponse({
                    'status': 'success',
                    'payment_status': payment.status,
                    'amount': str(payment.amount),
                    'payment_method': payment.payment_method,
                    'transaction_id': payment.transaction_id
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Ödeme kaydı bulunamadı'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@csrf_exempt
def call_waiter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        table_number = data.get('table_number')
        
        # Get table and assigned waiter
        table = get_object_or_404(Table, table_number=table_number)
        waiter = table.user
        
        if waiter:
            # Here you would typically send a notification to the waiter
            # For now, we'll just return success
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No waiter assigned to this table'})

@csrf_exempt
def cancel_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        # Get order
        order = get_object_or_404(Order, order_id=order_id)
        
        # Only allow cancellation if status is 'received'
        if order.status == 'received':
            order.delete()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Order cannot be cancelled'})

@csrf_exempt
def assign_server(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_id = data.get('table_id')
            server_id = data.get('server_id')
            
            table = get_object_or_404(Table, table_id=table_id)
            server = get_object_or_404(Users, user_id=server_id, user_type='waiter')
            
            table.user = server
            table.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Garson başarıyla atandı'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@csrf_exempt
def cart_summary(request, table_number):
    if request.method == 'GET':
        try:
            table = get_object_or_404(Table, table_number=table_number)
            cart = Cart.objects.filter(table=table, is_active=True).first()
            
            if not cart:
                return JsonResponse({
                    'items': [],
                    'total': 0
                })
            
            cart_items = Cartitem.objects.filter(cart=cart).order_by('cartitem_id')
            items = []
            total = 0
            
            for item in cart_items:
                quantity = item.quantity if item.quantity is not None else 0
                unit_price = item.unit_price if item.unit_price is not None else 0
                item_total = quantity * unit_price
                total += item_total
                items.append({
                    'item_id': item.item.item_id,
                    'name': item.item.name,
                    'quantity': quantity,
                    'unit_price': float(unit_price),
                    'total_price': float(item_total)
                })
            
            return JsonResponse({
                'items': items,
                'total': float(total)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@csrf_exempt
def get_order_details(request, order_id):
    if request.method == 'GET':
        try:
            order = get_object_or_404(Order, order_id=order_id)
            items = Orderitem.objects.filter(order=order)
            
            total_amount = sum((item.quantity if item.quantity is not None else 0) * (item.unit_price if item.unit_price is not None else 0) for item in items)
            
            return JsonResponse({
                'status': 'success',
                'items': [{
                    'name': item.item.name,
                    'quantity': item.quantity if item.quantity is not None else 0,
                    'price': str(item.unit_price if item.unit_price is not None else 0),
                    'total': str((item.quantity if item.quantity is not None else 0) * (item.unit_price if item.unit_price is not None else 0))
                } for item in items],
                'total_amount': str(total_amount)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        return redirect('home')  # Yönetici değilse ana sayfaya yönlendir
    return render(request, 'restaurant/manager_dashboard.html')

@csrf_exempt
@csrf_exempt
def remove_from_cart(request, table_number):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            # Get table
            table = get_object_or_404(Table, table_number=table_number)
            
            # Get active cart
            cart = Cart.objects.filter(table=table, is_active=True).first()
            if not cart:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Aktif sepet bulunamadı'
                }, status=404)
            
            # Get menu item
            menu_item = get_object_or_404(Menuitem, item_id=item_id)
            
            # Get cart item
            cart_item = Cartitem.objects.filter(cart=cart, item=menu_item).first()
            if cart_item:
                if cart_item.quantity > 1:
                    # Miktarı 1 azalt
                    cart_item.quantity = (cart_item.quantity if cart_item.quantity is not None else 0) - 1
                    cart_item.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': f'{menu_item.name} adedi 1 azaltıldı'
                    })
                else:
                    # Miktar 1 ise ürünü tamamen sil
                    cart_item.delete()
                    return JsonResponse({
                        'status': 'success',
                        'message': f'{menu_item.name} sepetten çıkarıldı'
                    })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Ürün sepette bulunamadı'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@login_required
def table_orders_api(request, table_id):
    table = get_object_or_404(Table, table_id=table_id)
    orders = Order.objects.filter(table=table).order_by('-created_at')
    orders_data = []
    for order in orders:
        orders_data.append({
            'order_id': order.order_id,
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse({'orders': orders_data})

@csrf_exempt
def delete_order(request, table_id, order_id):
    if request.method == 'POST':
        from .models import Order, Orderitem
        order = get_object_or_404(Order, order_id=order_id, table_id=table_id)
        if order.status == 'completed':
            # Önce orderitem'ları sil
            Orderitem.objects.filter(order=order).delete()
            order.delete()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Sadece tamamlanmış siparişler silinebilir!'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek metodu'}, status=405)

@login_required
def pending_cash_payments(request):
    # Sadece garsonlar erişebilir
    try:
        # Önce Users modelinden kullanıcıyı bul
        users_instance = Users.objects.get(username=request.user.username)
        # Sonra Staff modelinden staff'ı bul
        staff = Staff.objects.get(user=users_instance)
        if staff.user_type != 'waiter':
            messages.error(request, 'Bu sayfaya sadece garsonlar erişebilir.')
            return redirect('permission_denied')
    except (Users.DoesNotExist, Staff.DoesNotExist):
        messages.error(request, 'Bu sayfaya sadece garsonlar erişebilir.')
        return redirect('permission_denied')
    
    # Garsonun onay bekleyen nakit ödemeleri
    pending_payments = Payment.objects.filter(
        payment_method='cash',
        status='waiter_approval',
    ).select_related('order', 'order__table').order_by('-created_at')
    
    return render(request, 'base/pending_cash_payments.html', {
        'pending_payments': pending_payments
    })

@login_required
@require_POST
def approve_cash_payment(request, payment_id):
    try:
        # Önce Users modelinden kullanıcıyı bul
        users_instance = Users.objects.get(username=request.user.username)
        # Sonra Staff modelinden staff'ı bul
        staff = Staff.objects.get(user=users_instance)
        if staff.user_type != 'waiter':
            return JsonResponse({'status': 'error', 'message': 'Yetkisiz erişim'}, status=403)
    except (Users.DoesNotExist, Staff.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Yetkisiz erişim'}, status=403)
    
    try:
        payment = Payment.objects.get(id=payment_id, status='waiter_approval')
        
        data = json.loads(request.body)
        cash_received = Decimal(data.get('cash_received', '0'))
        
        if cash_received < payment.amount:
            return JsonResponse({
                'status': 'error',
                'message': 'Alınan nakit tutarı, ödeme tutarından az olamaz'
            }, status=400)
        
        # Ödemeyi onayla
        payment.status = 'completed'
        payment.waiter = staff
        payment.waiter_approval_time = timezone.now()
        payment.cash_received = cash_received
        payment.cash_returned = cash_received - payment.amount
        payment.save()
        
        # Siparişi tamamlandı olarak işaretle
        order = payment.order
        order.status = 'completed'
        order.save()
        
        # Masanın durumunu kontrol et
        table = order.table
        if not Order.objects.filter(table=table, status__in=['received', 'preparing', 'ready']).exists():
            table.table_status = 'available'
            table.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Ödeme başarıyla onaylandı'
        })
        
    except Payment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Ödeme bulunamadı'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Geçersiz veri formatı'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def get_pending_payments_count(request):
    try:
        # Önce Users modelinden kullanıcıyı bul
        users_instance = Users.objects.get(username=request.user.username)
        # Sonra Staff modelinden staff'ı bul
        staff = Staff.objects.get(user=users_instance)
        if staff.user_type != 'waiter':
            return JsonResponse({'count': 0})
    except (Users.DoesNotExist, Staff.DoesNotExist):
        return JsonResponse({'count': 0})
    
    count = Payment.objects.filter(
        payment_method='cash',
        status='waiter_approval'
    ).count()
    
    return JsonResponse({'count': count})

@login_required
@require_POST
def add_server(request):
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            # Django User oluştur
            django_user = DjangoUser.objects.create_user(
                username=data['username'],
                password=data['password'],
                first_name=data['fullname']
            )
            # Kullanıcı oluştur
            user = Users.objects.create(
                fullname=data['fullname'],
                username=data['username'],
                password=make_password(data['password']),
                phone_number=data.get('phone_number'),
                user_type='waiter',
                role='waiter'
            )
            # Staff kaydı oluştur
            staff = Staff.objects.create(
                user=user,
                user_type='waiter'
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Garson başarıyla eklendi'
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
def bulk_delete_orders(request, table_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_ids = data.get('order_ids', [])
            if not order_ids:
                return JsonResponse({'status': 'error', 'message': 'Hiçbir sipariş seçilmedi!'}, status=400)
            deleted_count = 0
            for oid in order_ids:
                try:
                    order = Order.objects.get(order_id=oid, table_id=table_id, status='completed')
                    Orderitem.objects.filter(order=order).delete()
                    order.delete()
                    deleted_count += 1
                except Order.DoesNotExist:
                    continue
            if deleted_count > 0:
                return JsonResponse({'status': 'success', 'message': f'{deleted_count} sipariş silindi.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Hiçbir sipariş silinemedi!'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek metodu'}, status=405)

@csrf_exempt
def remove_waiter(request, table_id):
    if request.method == 'POST':
        try:
            table = Table.objects.get(table_id=table_id)
            table.user = None
            table.save()
            return JsonResponse({'status': 'success', 'message': 'Garson kaldırıldı'})
        except Table.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Masa bulunamadı!'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek metodu'}, status=405)

# Create your views here.
