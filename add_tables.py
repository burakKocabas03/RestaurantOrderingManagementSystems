import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from base.models import Table, Order, Orderitem, Cart, Cartitem
from django.db import connection

# Önce ilişkili tüm kayıtları sil
Orderitem.objects.all().delete()
Cartitem.objects.all().delete()
Order.objects.all().delete()
Cart.objects.all().delete()
Table.objects.all().delete()

# Önce foreign key constraint'i devre dışı bırak
with connection.cursor() as cursor:
    cursor.execute("SET CONSTRAINTS ALL DEFERRED;")

# Constraint'i tekrar aktif et
with connection.cursor() as cursor:
    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE;")

# Tabloları oluştur
tables = [
    {'table_number': 1, 'table_status': 'available'},
    {'table_number': 2, 'table_status': 'available'},
    {'table_number': 3, 'table_status': 'available'},
    {'table_number': 4, 'table_status': 'available'},
    {'table_number': 5, 'table_status': 'available'},
    {'table_number': 6, 'table_status': 'available'},
    {'table_number': 7, 'table_status': 'available'},
    {'table_number': 8, 'table_status': 'available'},
    {'table_number': 9, 'table_status': 'available'},
    {'table_number': 10, 'table_status': 'available'},
]

# Tabloları ekle
for i, table_data in enumerate(tables, 1):
    Table.objects.create(
        table_id=i,
        table_number=table_data['table_number'],
        table_status=table_data['table_status']
    )

print("Tablolar başarıyla eklendi!") 