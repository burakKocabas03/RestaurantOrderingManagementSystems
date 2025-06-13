from django.contrib import admin
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
import json
from datetime import timedelta, date
from .models import Ingredient, SalesReport, Staff, Menuitem, Orderitem

# Register your models here.

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_quantity', 'minimum_stock', 'unit', 'created_at')
    search_fields = ('name',)
    list_filter = ('unit',)

@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sales', 'total_orders', 'total_profit', 'average_order_value')
    list_filter = ('date',)
    search_fields = ('date',)
    readonly_fields = ('total_sales', 'total_orders', 'total_profit', 'average_order_value', 'popular_items', 'created_at')
    ordering = ('-date',)
    change_list_template = 'admin/base/salesreport/change_list.html'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Son 30 günün verilerini al
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        next_seven_days = today + timedelta(days=7)  # Gelecek 7 günü de göster
        
        # Tüm tarihleri oluştur (geçmiş 30 gün + bugün + gelecek 7 gün)
        all_dates = []
        current_date = thirty_days_ago
        while current_date <= next_seven_days:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Tarih aralığındaki tüm raporları al
        reports = SalesReport.objects.filter(
            date__gte=thirty_days_ago,
            date__lte=today
        ).order_by('date')
        
        # Raporları sözlüğe dönüştür
        reports_dict = {report.date: report for report in reports}
        
        # Grafik verilerini hazırla
        dates = []
        sales_data = []
        orders_data = []
        
        for date in all_dates:
            dates.append(date.strftime('%d/%m/%Y'))
            if date in reports_dict:
                report = reports_dict[date]
                sales_data.append(float(report.total_sales))
                orders_data.append(report.total_orders)
            else:
                sales_data.append(0)
                orders_data.append(0)
        
        # Popüler ürünlerin verilerini al (son 30 gün)
        popular_items = Orderitem.objects.filter(
            order__status='completed',
            order__created_at__date__gte=thirty_days_ago,
            order__created_at__date__lte=today
        ).values(
            'item__name'
        ).annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:5]
        
        popular_items_labels = [item['item__name'] for item in popular_items]
        popular_items_data = [item['total_quantity'] for item in popular_items]
        
        # Bugünün verilerini al
        today_report = SalesReport.objects.filter(date=today).first()
        
        extra_context = extra_context or {}
        if today_report:
            extra_context.update({
                'today_total_sales': str(today_report.total_sales),
                'today_total_orders': today_report.total_orders,
                'today_average_order': str(today_report.average_order_value),
                'today_total_profit': str(today_report.total_profit),
            })
        else:
            extra_context.update({
                'today_total_sales': '0.00',
                'today_total_orders': 0,
                'today_average_order': '0.00',
                'today_total_profit': '0.00',
            })
        
        # Grafik verilerini context'e ekle
        extra_context.update({
            'dates': json.dumps(dates),
            'sales_data': json.dumps(sales_data),
            'orders_data': json.dumps(orders_data),
            'popular_items_labels': json.dumps(popular_items_labels),
            'popular_items_data': json.dumps(popular_items_data),
        })
        
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('user_type',)

@admin.register(Menuitem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_avaible')
    search_fields = ('name',)
    list_filter = ('category', 'is_avaible')