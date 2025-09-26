import { Product } from '../types';
import api from './api';

export interface Order {
  id: number;
  order_number: string;
  status: 'processing' | 'shipped' | 'delivered' | 'cancelled';
  total_amount: number;
  shipping_address: string;
  billing_address: string;
  payment_id: string;
  payment_status: 'pending' | 'succeeded' | 'failed';
  created_at: string;
  updated_at: string;
  user: number;
  items: Array<{
    id: number;
    order: number;
    product: Product;
    quantity: number;
    price: number;
  }>;
}

export interface CreateOrderData {
  payment_intent_id: string;
  shipping_address: string;
  billing_address: string;
}
export interface CreatePaymentIntentData {
  amount: number;
  currency: string;
}

// API Response model
export interface OrdersResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Order[];
}

export const orderService = {
  async getOrders(): Promise<OrdersResponse> {
    const response = await api.get('/orders/');
    console.log('Fetched orders:', response.data);
    return response.data;
  },

  async getOrder(id: number): Promise<Order> {
    const response = await api.get(`/orders/${id}/`);
    return response.data;
  },

  async createOrder(data: CreateOrderData): Promise<Order> {
    const response = await api.post('/orders/create/', data);
    return response.data;
  },
  async getPaymentIntent(data: CreatePaymentIntentData): Promise<{ clientSecret: string; }> {
    const response = await api.post('/orders/create_payment_intent/', data);
    return response.data;
  },
  async downloadInvoice(orderId: number) {
    // /http://127.0.0.1:8000/api/orders/1/invoice/
    const response = await api.get(`/orders/${orderId}/invoice/`, {
      responseType: 'blob', // important for files
    });

    // create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `invoice-${orderId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};