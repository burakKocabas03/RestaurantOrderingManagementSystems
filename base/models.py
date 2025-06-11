# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractUser, User


class Allergens(models.Model):
    allerg_id = models.IntegerField(primary_key=True)
    allerg_name = models.CharField(max_length=100)
    allerg_description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'allergens'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    table = models.ForeignKey('Table', models.DO_NOTHING, blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'cart'


class Cartitem(models.Model):
    cartitem_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    cart = models.ForeignKey(Cart, models.DO_NOTHING)
    item = models.ForeignKey('Menuitem', models.DO_NOTHING)
    quantity = models.IntegerField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cartitem'


class Category(models.Model):
    category_id = models.IntegerField(primary_key=True)
    category_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'category'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class HasAllergens(models.Model):
    pk = models.CompositePrimaryKey('allerg_id', 'item_id')
    allerg = models.ForeignKey(Allergens, models.DO_NOTHING)
    item = models.ForeignKey('Menuitem', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'has_allergens'


class Ingredients(models.Model):
    ing_id = models.IntegerField(primary_key=True)
    ing_name = models.CharField(max_length=100)
    is_allergen = models.BooleanField()
    unit = models.CharField(max_length=20, blank=True, null=True)
    is_avaible = models.BooleanField()
    quantity = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ingredients'


class MakesWith(models.Model):
    pk = models.CompositePrimaryKey('ing_id', 'item_id')
    ing = models.ForeignKey(Ingredients, models.DO_NOTHING)
    item = models.ForeignKey('Menuitem', models.DO_NOTHING)
    quantity_required = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'makes_with'


class Menuitem(models.Model):
    item_id = models.IntegerField(primary_key=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_avaible = models.BooleanField()
    rate_count = models.IntegerField(blank=True, null=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    calories = models.IntegerField(blank=True, null=True)
    category = models.ForeignKey(Category, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'menuitem'


class Order(models.Model):
    order_id = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    delivery_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    table = models.ForeignKey('Table', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order'


class Orderitem(models.Model):
    pk = models.CompositePrimaryKey('order_id', 'item_id')
    order = models.ForeignKey(Order, models.DO_NOTHING)
    item = models.ForeignKey(Menuitem, models.DO_NOTHING)
    quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orderitem'


class Table(models.Model):
    table_id = models.IntegerField(primary_key=True)
    table_number = models.IntegerField()
    table_status = models.CharField(max_length=50, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'table_'


class Users(models.Model):
    user_id = models.IntegerField(primary_key=True)
    fullname = models.CharField(max_length=100)
    username = models.CharField(unique=True, max_length=50)
    password = models.CharField(max_length=100)
    start_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    user_type = models.CharField(max_length=30, blank=True, null=True)
    tip_ballance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    permission = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=[('customer', 'Müşteri'), ('waiter', 'Garson'), ('manager', 'Yönetici')], default='customer')

    class Meta:
        managed = False
        db_table = 'users'


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Nakit'),
        ('credit_card', 'Kredi Kartı'),
        ('in_app', 'Uygulama İçi Ödeme')
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Beklemede'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız')
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payment for Order #{self.order.order_id} - {self.amount} TL"


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # kg, lt, adet vs.
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SalesReport(models.Model):
    date = models.DateField()
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)
    popular_items = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sales Report for {self.date}"


class Staff(models.Model):
    ROLES = (
        ('manager', 'Yönetici'),
        ('waiter', 'Garson'),
        ('kitchen', 'Mutfak'),
    )
    
    user = models.OneToOneField('Users', on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=ROLES)
    schedule = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta:
        managed = True
        db_table = 'base_staff'
