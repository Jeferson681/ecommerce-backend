export type OrderItem = {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  price: string;
  created_at: string;
  updated_at: string;
};

export type Order = {
  id: number;
  user_id: number;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
};
