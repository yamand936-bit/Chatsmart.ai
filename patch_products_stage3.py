with open("frontend/src/app/app/products/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    "import toast from 'react-hot-toast';",
    "import toast from 'react-hot-toast';\nimport { ProductCardSkeleton } from '@/components/Skeleton';"
)

text = text.replace(
    "const [products, setProducts] = useState<any[]>([]);",
    "const [products, setProducts] = useState<any[]>([]);\n  const [loading, setLoading] = useState(true);"
)

old_fetch = """  const fetchProducts = async () => {
    try {
        const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true });
        setProducts(res.data.data || []);
    } catch (err) {
        console.error(err);
        toast.error('Failed to load products');
    }
  };"""
new_fetch = """  const fetchProducts = async () => {
    setLoading(true);
    try {
        const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true });
        setProducts(res.data.data || []);
    } catch (err) {
        console.error(err);
        toast.error('Failed to load products');
    } finally {
        setLoading(false);
    }
  };"""

text = text.replace(old_fetch, new_fetch)

old_jsx = """      {products.length === 0 ? ("""
new_jsx = """      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {Array.from({length: 6}).map((_,i) => <ProductCardSkeleton key={i} />)}
        </div>
      ) : products.length === 0 ? ("""

text = text.replace(old_jsx, new_jsx)

with open("frontend/src/app/app/products/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
