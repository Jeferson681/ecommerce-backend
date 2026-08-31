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

export type ProductPage = {
  items: Product[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
};
