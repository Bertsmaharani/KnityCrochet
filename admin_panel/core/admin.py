from django.contrib import admin
from django import forms
from .models import Role, User, Supplier, Product, Order, OrderProduct, Review

# Форма для скрытия пароля звездочками в админке
class UserAdminForm(forms.ModelForm):
    user_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True), 
        label="Пароль"
    )
    
    class Meta:
        model = User
        fields = '__all__'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ('user_id', 'user_login', 'first_name', 'last_name', 'email', 'role')
    search_fields = ('user_login', 'first_name', 'last_name', 'email')
    list_filter = ('role',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_name', 'category_name', 'price', 'stock_quantity', 'supplier')
    search_fields = ('product_name', 'category_name')
    list_filter = ('category_name', 'supplier')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'order_date', 'order_status', 'payment_method', 'delivery_address')
    list_filter = ('order_status', 'payment_method')
    search_fields = ('customer__last_name', 'delivery_address')

admin.site.register(Role)
admin.site.register(Supplier)
admin.site.register(OrderProduct)
admin.site.register(Review)

# Заголовки
admin.site.site_header = "Панель управления Knity Crochet"
admin.site.site_title = "Knity Crochet Admin"
admin.site.index_title = "Управление магазином"