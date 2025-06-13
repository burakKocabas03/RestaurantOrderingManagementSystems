# Restaurant Ordering Management System

Bu proje, bir restoran için sipariş yönetim sistemi uygulamasıdır. Django framework'ü kullanılarak geliştirilmiştir.

## Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- Git
- PostgreSQL

## Kurulum Adımları

1. Projeyi klonlayın:
```bash
git clone https://github.com/burakKocabas03/RestaurantOrderingManagementSystems.git
cd RestaurantOrderingManagementSystems
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
# Windows için:
python -m venv venv
venv\Scripts\activate

# macOS/Linux için:
python3 -m venv venv
source venv/bin/activate
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Veritabanı Ayarları:
`config/settings.py` dosyasında PostgreSQL ayarlarını yapılandırın:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'restaurant_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

5. Veritabanı migrasyonlarını yapın:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Örnek verileri yükleyin:
```bash
python add_menu_items.py
python add_tables.py
```

7. Geliştirme sunucusunu başlatın:
```bash
python manage.py runserver
```

Uygulama http://127.0.0.1:8000/login adresinde çalışmaya başlatin .

## Özellikler

- Menü yönetimi
- Sipariş takibi
- Masa yönetimi
- Personel yönetimi
- Satış raporları

## Kullanıcı Rolleri

1. Yönetici (Admin)
   - Tüm sisteme erişim
   - Personel yönetimi
   - Raporlama

2. Personel
   - Sipariş alma
   - Masa yönetimi
   - Temel işlemler

## Teknik Detaylar

- Django 4.2
- PostgreSQL veritabanı
- Bootstrap ile responsive tasarım
- Django template engine

## İletişim
burak.kocabas2003@hotmail.com
Sorularınız veya önerileriniz için GitHub üzerinden issue açabilirsiniz.