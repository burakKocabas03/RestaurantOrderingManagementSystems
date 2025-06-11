from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Menuitem, Category, Order, Orderitem, Table, Cart, Cartitem, Users, Payment
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime, timezone
from django.db import models
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import connection
import time

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
        django_user = User.objects.create_user(
            username=username,
            password=password,
            first_name=fullname
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
                    django_user = User.objects.get(username=username)
                except User.DoesNotExist:
                    # Django user yoksa oluştur
                    django_user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=custom_user.fullname
                    )
                
                login(request, django_user)
                
                # Kullanıcı tipine göre yönlendirme
                if custom_user.user_type == 'waiter':
                    return redirect('table_management')
                elif custom_user.user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('menu')
            else:
                return render(request, 'login.html', {'error': 'Invalid password'})
                
        except Users.DoesNotExist:
            return render(request, 'login.html', {'error': 'User not found'})
            
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

@user_passes_test(is_waiter)
def table_management(request):
    tables = Table.objects.all()
    servers = Users.objects.filter(user_type='waiter')
    return render(request, 'table_management.html', {
        'tables': tables,
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
                    order_item, created = Orderitem.objects.get_or_create(
                        order=order,
                        item=cart_item.item,
                        defaults={
                            'quantity': cart_item.quantity,
                            'unit_price': cart_item.unit_price,
                            'notes': cart_item.notes
                        }
                    )
                    if not created:
                        order_item.quantity += cart_item.quantity
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
    ).order_by('created_at')
    
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
            
            # Seçilen siparişleri işle
            orders = Order.objects.filter(order_id__in=order_ids)
            table = orders.first().table  # İlk siparişin masasını al
            
            # Her sipariş için ödeme kaydı oluştur
            for order in orders:
                payment = Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method=payment_method,
                    status='completed',
                    transaction_id=f"TRX{int(time.time())}"
                )
                
                # Siparişi tamamlandı olarak işaretle
                order.status = 'completed'
                order.save()
            
            # Masanın tüm siparişleri tamamlandı mı kontrol et
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
            
            cart_items = Cartitem.objects.filter(cart=cart)
            items = []
            total = 0
            
            for item in cart_items:
                item_total = item.quantity * item.unit_price
                total += item_total
                items.append({
                    'item_id': item.item.item_id,
                    'name': item.item.name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
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
            
            total_amount = sum(item.quantity * item.unit_price for item in items)
            
            return JsonResponse({
                'status': 'success',
                'items': [{
                    'name': item.item.name,
                    'quantity': item.quantity,
                    'price': str(item.unit_price),
                    'total': str(item.quantity * item.unit_price)
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
                    cart_item.quantity -= 1
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
# Create your views here.
