export type Product = {
  id: number;
  name: string;
  description: string | null;
  category: string | null;
  image_url: string | null;
  price: string;
  stock_quantity: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
