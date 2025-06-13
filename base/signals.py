from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from decimal import Decimal
from .models import Order, SalesReport, Orderitem

@receiver(post_save, sender=Order)
def update_sales_report(sender, instance, **kwargs):
    if instance.status == 'completed':
        try:
            today = timezone.now().date()
            
            # Günün raporunu bul veya oluştur
            report, created = SalesReport.objects.get_or_create(
                date=today,
                defaults={
                    'total_sales': Decimal('0.00'),
                    'total_orders': 0,
                    'total_profit': Decimal('0.00'),
                    'average_order_value': Decimal('0.00')
                }
            )
            
            # Tamamlanmış siparişlerin verilerini hesapla
            completed_orders = Order.objects.filter(
                status='completed',
                created_at__date=today
            )
            
            # Toplam satış ve sipariş sayısı
            total_sales = Decimal('0.00')
            for order in completed_orders:
                order_items = Orderitem.objects.filter(order=order)
                for item in order_items:
                    if item.quantity and item.unit_price:
                        total_sales += item.quantity * item.unit_price
            
            total_orders = completed_orders.count()
            
            # Ortalama sipariş değeri
            average_order_value = total_sales / total_orders if total_orders > 0 else Decimal('0.00')
            
            # Popüler ürünleri hesapla
            popular_items = Orderitem.objects.filter(
                order__status='completed',
                order__created_at__date=today
            ).values(
                'item__name'
            ).annotate(
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:5]
            
            # Tahmini kârı hesapla (örnek olarak %20 kâr marjı)
            total_profit = total_sales * Decimal('0.20')
            
            # Raporu güncelle
            report.total_sales = total_sales
            report.total_orders = total_orders
            report.total_profit = total_profit
            report.average_order_value = average_order_value
            report.popular_items = '\n'.join([
                f"{item['item__name']}: {item['total_quantity']} adet"
                for item in popular_items
            ])
            report.save()
        except Exception as e:
            print(f"Satış raporu güncellenirken hata oluştu: {str(e)}") 