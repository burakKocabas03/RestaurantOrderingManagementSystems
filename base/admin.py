from django.contrib import admin
from .models import Ingredient, SalesReport, Staff, Menuitem

# Register your models here.

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_quantity', 'minimum_stock', 'unit', 'created_at')
    search_fields = ('name',)
    list_filter = ('unit',)

@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sales', 'created_at')
    search_fields = ('date',)

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