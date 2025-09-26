from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Order, Cart, CartItem
from .serializers import OrderSerializer, CartSerializer, CartItemSerializer
from products.models import Product
import uuid
import stripe
from .models import Order, OrderItem, Cart, CartItem
import os
from django.http import FileResponse, Http404
from reportlab.pdfgen import canvas
from io import BytesIO

stripe.api_key = settings.STRIPE_SECRET_KEY

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    
    try:
        product = Product.objects.get(id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        quantity = request.data.get('quantity', 1)
        
        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        cart = cart_item.cart
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()
        
        cart = Cart.objects.get(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    
    
    try:
        payment_intent_id = request.data.get("payment_intent_id")
        if not payment_intent_id:
            return Response({"error": "Missing payment_intent_id"}, status=status.HTTP_400_BAD_REQUEST)
        # 1. Verify payment intent
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status != "succeeded":
            return Response({"error": "Payment not completed"}, status=status.HTTP_400_BAD_REQUEST)
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order
        order = Order.objects.create(
            
            # user=request.user,
            # order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            # total_amount=sum(item.product.price * item.quantity for item in cart.items.all()),
            # shipping_address=request.data.get('shipping_address', ''),
            # billing_address=request.data.get('billing_address', ''),
            user=request.user,
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            total_amount=sum(item.product.price * item.quantity for item in cart.items.all()),
            shipping_address=request.data.get("shipping_address", ""),
            billing_address=request.data.get("billing_address", ""),
            payment_id=payment_intent_id,  # Save Stripe payment id
            status= Order.STATUS_Processing
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Clear cart
        cart.items.all().delete()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    # console.log("Creating payment intent")
    try:
        cart = Cart.objects.get(user=request.user)
        print(cart)
        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        amount = int(sum(item.product.price * item.quantity for item in cart.items.all()) * 100)  # in cents
        print("Payment amount (cents):", amount)

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={"user_id": request.user.id},
        )

        return Response({"clientSecret": intent.client_secret})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_invoice(request, order_id):   
    print("✅ download_invoice called with order_id =", order_id)  # 👈 debug log 
    order = get_object_or_404(Order, id=order_id, user=request.user)

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, f"Invoice for Order {order.order_number}")
    p.drawString(100, 780, f"Total: {order.total_amount}")
    p.drawString(100, 760, f"Status: {order.status}")
    p.showPage()
    p.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f"invoice-{order_id}.pdf")

    # # assume invoices are stored inside MEDIA_ROOT/invoices/
    # invoice_path = os.path.join(settings.MEDIA_ROOT, "invoices", "2.pdf")

    # print("🔍 Checking for invoice at:", invoice_path)

    # if not os.path.exists(invoice_path):
    #     raise Http404("Invoice not found")

    # return FileResponse(open(invoice_path, "rb"), content_type="application/pdf")