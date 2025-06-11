import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from base.models import Category, Menuitem, Orderitem, MakesWith, HasAllergens
from django.db import connection

# Önce ilişkili tüm kayıtları sil
Orderitem.objects.all().delete()
MakesWith.objects.all().delete()
HasAllergens.objects.all().delete()
Menuitem.objects.all().delete()
Category.objects.all().delete()

# Önce foreign key constraint'i devre dışı bırak
with connection.cursor() as cursor:
    cursor.execute("SET CONSTRAINTS ALL DEFERRED;")

# Constraint'i tekrar aktif et
with connection.cursor() as cursor:
    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE;")

# Kategorileri oluştur
categories = {
    'Ana Yemekler': [
        {'name': 'Izgara Köfte', 'price': 180.00, 'description': 'Özel baharatlarla hazırlanmış ızgara köfte, pilav ve közlenmiş domates ile', 'calories': 650},
        {'name': 'Tavuk Şiş', 'price': 160.00, 'description': 'Marine edilmiş tavuk şiş, pilav ve közlenmiş sebzeler ile', 'calories': 550},
        {'name': 'Pide', 'price': 120.00, 'description': 'Kıymalı, kuşbaşılı veya kaşarlı pide seçenekleri', 'calories': 450},
        {'name': 'Lahmacun', 'price': 45.00, 'description': 'İnce hamur üzerine kıymalı harç ile', 'calories': 300},
        {'name': 'Karnıyarık', 'price': 140.00, 'description': 'Patlıcan karnıyarık, pilav ile', 'calories': 500},
    ],
    'Çorbalar': [
        {'name': 'Mercimek Çorbası', 'price': 45.00, 'description': 'Geleneksel mercimek çorbası', 'calories': 200},
        {'name': 'Ezogelin Çorbası', 'price': 45.00, 'description': 'Özel baharatlarla hazırlanmış ezogelin çorbası', 'calories': 220},
        {'name': 'İşkembe Çorbası', 'price': 55.00, 'description': 'Sarımsaklı işkembe çorbası', 'calories': 250},
    ],
    'İçecekler': [
        {'name': 'Türk Kahvesi', 'price': 35.00, 'description': 'Geleneksel Türk kahvesi', 'calories': 5},
        {'name': 'Çay', 'price': 15.00, 'description': 'Taze demlenmiş çay', 'calories': 2},
        {'name': 'Ayran', 'price': 20.00, 'description': 'Soğuk ayran', 'calories': 50},
        {'name': 'Kola', 'price': 25.00, 'description': 'Soğuk kola', 'calories': 140},
        {'name': 'Limonata', 'price': 35.00, 'description': 'Taze sıkılmış limonata', 'calories': 120},
    ],
    'Tatlılar': [
        {'name': 'Künefe', 'price': 85.00, 'description': 'Antep fıstıklı künefe', 'calories': 450},
        {'name': 'Baklava', 'price': 75.00, 'description': 'Fıstıklı baklava', 'calories': 400},
        {'name': 'Sütlaç', 'price': 45.00, 'description': 'Fırında sütlaç', 'calories': 250},
        {'name': 'Kazandibi', 'price': 45.00, 'description': 'Geleneksel kazandibi', 'calories': 280},
    ],
    'Atıştırmalıklar': [
        {'name': 'Patates Kızartması', 'price': 45.00, 'description': 'Çıtır patates kızartması', 'calories': 350},
        {'name': 'Soğan Halkası', 'price': 40.00, 'description': 'Çıtır soğan halkası', 'calories': 300},
        {'name': 'Nugget', 'price': 55.00, 'description': 'Tavuk nugget, sos ile', 'calories': 400},
        {'name': 'Mozarella Çubukları', 'price': 65.00, 'description': 'Çıtır mozarella çubukları, sos ile', 'calories': 450},
    ],
    'Salatalar': [
        {'name': 'Çoban Salata', 'price': 45.00, 'description': 'Domates, salatalık, biber, soğan', 'calories': 150},
        {'name': 'Sezar Salata', 'price': 65.00, 'description': 'Marul, tavuk, kruton, parmesan', 'calories': 300},
        {'name': 'Akdeniz Salata', 'price': 55.00, 'description': 'Yeşillikler, zeytin, peynir', 'calories': 200},
    ]
}

# Kategorileri ve ürünleri ekle
category_id = 1
item_id = 1
for category_name, items in categories.items():
    # Kategoriyi oluştur
    category = Category.objects.create(
        category_id=category_id,
        category_name=category_name
    )
    category_id += 1
    
    # Kategoriye ait ürünleri ekle
    for item in items:
        Menuitem.objects.create(
            item_id=item_id,
            name=item['name'],
            price=item['price'],
            description=item['description'],
            calories=item['calories'],
            category=category,
            is_avaible=True
        )
        item_id += 1

print("Menü öğeleri başarıyla eklendi!") 