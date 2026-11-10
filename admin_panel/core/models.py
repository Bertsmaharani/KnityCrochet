from django.db import models
from django.contrib.auth.hashers import make_password

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.TextField()

    class Meta:
        managed = False
        db_table = 'Roles'
    
    def __str__(self):
        return self.role_name

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, models.DO_NOTHING, db_column='role_id', blank=True, null=True)
    user_login = models.TextField(unique=True)
    user_password = models.TextField()
    first_name = models.TextField()
    last_name = models.TextField()
    patronym = models.TextField(blank=True, null=True)
    email = models.TextField()
    phone = models.TextField()
    birth_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'Users'

    def save(self, *args, **kwargs):
        if self.user_password and not self.user_password.startswith('pbkdf2_sha256$'):
            self.user_password = make_password(self.user_password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.user_login})"

class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    manager = models.ForeignKey(User, models.DO_NOTHING, db_column='manager_id')
    supplier_name = models.TextField()
    contact_info = models.TextField()

    class Meta:
        managed = False
        db_table = 'Suppliers'

    def __str__(self):
        return self.supplier_name

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, models.DO_NOTHING, db_column='supplier_id')
    product_name = models.TextField()
    category_name = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Products'

    def __str__(self):
        return self.product_name

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    manager = models.ForeignKey(User, models.DO_NOTHING, db_column='manager_id', related_name='managed_orders', blank=True, null=True)
    customer = models.ForeignKey(User, models.DO_NOTHING, db_column='customer_id', related_name='customer_orders')
    order_date = models.DateField()
    delivery_address = models.TextField()
    order_status = models.TextField()
    payment_method = models.TextField()

    class Meta:
        managed = False
        db_table = 'Orders'
        
    def __str__(self):
        return f"Заказ #{self.order_id} от {self.customer.last_name}"

class OrderProduct(models.Model):
    order_product_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, models.DO_NOTHING, db_column='order_id')
    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='product_id')
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'OrderProducts'

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(User, models.DO_NOTHING, db_column='customer_id')
    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='product_id')
    rating = models.IntegerField()
    comment = models.TextField()
    review_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'Reviews'