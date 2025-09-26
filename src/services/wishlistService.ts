import api from './api';
import { Product } from '../types';

export interface WishlistResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: WishlistItem[];
}

export interface WishlistItem {
  id: number;
  product: Product;
  created_at: string;
}

export const wishlistService = {
  async getWishlist(): Promise<WishlistResponse> {
    const response = await api.get('/auth/wishlist/');
    return response.data;
  },

  async addToWishlist(productId: string): Promise<WishlistItem> {
    const response = await api.post('/auth/wishlist/', {
      product_id: productId,
    });
    return response.data;
  },

  async removeFromWishlist(productId: string): Promise<void> {
    await api.delete(`/auth/wishlist/remove/${productId}/`);
  },
};