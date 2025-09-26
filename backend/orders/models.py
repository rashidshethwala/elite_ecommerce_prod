from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Order(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'

    STATUS_Processing = 'processing'
    STATUS_Shipped = 'shipped'
    STATUS_Delivered = 'delivered'
    STATUS_Cancelled = 'cancelled'
    
    STATUS_CHOICES = [
        # ('processing', 'Processing'),
        # ('shipped', 'Shipped'),
        # ('delivered', 'Delivered'),
        # ('cancelled', 'Cancelled'),
        (STATUS_Processing, 'Processing'),
        (STATUS_Shipped, 'Shipped'),
        (STATUS_Delivered, 'Delivered'),
        (STATUS_Cancelled, 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        # ('pending', 'Pending'),
        # ('succeeded', 'Succeeded'),
        # ('failed', 'Failed'),
        # ('refunded', 'Refunded'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    billing_address = models.TextField()

    # Stripe fields
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # Stripe PaymentIntent ID
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"