import { ArrowLeft, ArrowRight, Compass, House, Tag, User, MapPin, MessageCircle, Phone, Search, ShieldCheck, ShoppingBag, Store } from 'lucide-react'
import { type FormEvent, useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Link, useLocation, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'

const API_BASE = 'https://sureplug-0q7j.onrender.com/api/v1';

type Category = { id: number; name: string; slug: string; description?: string }
type Campus = { id: number; name: string; zone: string; description: string }
type Vendor = {
  id: number;
  slug: string;
  business_name: string;
  description: string;
  phone?: string;
  whatsapp?: string;
  website?: string;
  campus_name?: string;
  location_description?: string;
  image?: string | null;
  is_verified?: boolean;
  username?: string;
}
type Product = {
  id: number;
  slug: string;
  name: string;
  description: string;
  price: string;
  currency: string;
  condition: string;
  availability: string;
  is_published: boolean;
  featured: boolean;
  image?: string | null;
  contact_phone?: string;
  whatsapp_number?: string;
  external_url?: string;
  price_updated_at: string;
  vendor?: Vendor;
  category?: Category;
  campus?: Campus;
  gallery?: Array<{ id: number; image: string }>
}

type VendorDashboard = {
  vendor: Vendor;
  stats: { published: number; unavailable: number; drafts: number; total: number };
  products: Product[];
}

const formatCurrency = (value: string | number) => `₦${Number(value).toLocaleString()}`

function csrfToken() {
  const cookie = document.cookie.split('; ').find((item) => item.startsWith('csrftoken='))
  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : ''
}

function errorMessage(payload: unknown, fallback: string) {
  if (payload && typeof payload === 'object') {
    const values = Object.values(payload as Record<string, unknown>)
    const message = values.flatMap((value) => Array.isArray(value) ? value : [value])
      .find((value) => typeof value === 'string')
    if (typeof message === 'string') return message
  }
  return fallback
}

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const token = csrfToken()
    if (token) headers.set('X-CSRFToken', token)
  }
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
    credentials: 'include',
  })
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null)
    throw new ApiError(errorMessage(payload, `Request failed (${response.status})`), response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

// WhatsApp links need the international format: 0803… becomes 234803…
function toWhatsAppNumber(raw: string) {
  const digits = raw.replace(/\D/g, '')
  if (digits.startsWith('234')) return digits
  if (digits.startsWith('0') && digits.length === 11) return `234${digits.slice(1)}`
  return digits
}

const RECENT_KEY = 'sureplug:recent'
function readRecent(): string[] {
  try {
    const value = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string').slice(0, 8) : []
  } catch { return [] }
}
function rememberProduct(slug: string) {
  try { localStorage.setItem(RECENT_KEY, JSON.stringify([slug, ...readRecent().filter((item) => item !== slug)].slice(0, 8))) } catch { /* storage unavailable */ }
}

function ImagePlaceholder({ className = '' }: { className?: string }) {
  return (
    <div role="img" aria-label="No photo available" className={`image-placeholder flex flex-col items-center justify-center gap-2 ${className}`}>
      <ShoppingBag className="h-8 w-8" />
      <span className="text-xs font-semibold">No photo available</span>
    </div>
  )
}

function RetryAlert({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="retry-alert flex flex-col gap-3 rounded-2xl border p-4 text-sm sm:flex-row sm:items-center sm:justify-between">
      <span>{message}</span>
      <button type="button" onClick={onRetry} className="retry-button shrink-0 rounded-full px-4 py-2 text-sm font-bold">Try again</button>
    </div>
  )
}

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: 'instant' }) }, [pathname])
  return null
}

function BottomNav() {
  const { pathname } = useLocation()
  if (pathname.startsWith('/product/')) return null
  const items = [
    { to: '/', label: 'Home', icon: House, active: pathname === '/' },
    { to: '/products', label: 'Explore', icon: Compass, active: pathname.startsWith('/product') },
    { to: '/vendors', label: 'Vendors', icon: Store, active: pathname.startsWith('/vendor') && pathname !== '/vendor-dashboard' },
    { to: '/dashboard', label: 'Account', icon: User, active: pathname.startsWith('/dashboard') },
  ]
  return (
    <nav aria-label="Main" className="bottom-nav md:hidden">
      {items.map(({ to, label, icon: Icon, active }) => (
        <Link key={to} to={to} aria-current={active ? 'page' : undefined} className={`bottom-nav-item ${active ? 'is-active' : ''}`}>
          <span className="bottom-nav-icon"><Icon className="h-5 w-5" /></span>{label}
        </Link>
      ))}
    </nav>
  )
}

function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/product/${product.slug}`} className="product-card group block overflow-hidden rounded-2xl border border-slate-200 bg-white transition duration-200 hover:-translate-y-1 hover:border-orange-300 hover:shadow-xl">
      <div className="product-card-image relative overflow-hidden bg-slate-100">
        {product.image ? <img src={product.image}
          alt={product.name}
          loading="lazy"
          className="h-48 w-full object-cover transition duration-300 group-hover:scale-105"
        /> : <ImagePlaceholder className="h-48 w-full" />}
        <span className="absolute left-3 top-3 rounded-full bg-white/95 px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm">{product.category?.name || 'General'}</span>
        {product.featured && <span className="absolute right-3 top-3 rounded-full bg-orange-500 px-3 py-1 text-xs font-semibold text-white">Featured</span>}
      </div>
      <div className="p-4">
        <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
          <span className="flex min-w-0 items-center gap-1 truncate"><MapPin className="h-3.5 w-3.5 shrink-0" />{product.campus?.name || product.vendor?.campus_name || 'Campus seller'}</span>
          <span className={`shrink-0 rounded-full px-2 py-1 font-medium ${product.availability === 'in_stock' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{product.availability.replaceAll('_', ' ')}</span>
        </div>
        <h3 className="mt-3 line-clamp-1 text-base font-bold text-slate-900 group-hover:text-orange-600">{product.name}</h3>
        <p className="mt-1 line-clamp-2 min-h-10 text-sm leading-5 text-slate-500">{product.description}</p>
        <div className="mt-4 flex items-end justify-between border-t border-slate-100 pt-4">
          <div>
            <div className="text-xl font-black tracking-tight text-slate-900">{formatCurrency(product.price)}</div>
            <div className="mt-1 text-xs text-slate-400">{product.vendor?.business_name || 'Local vendor'}</div>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition group-hover:bg-orange-500">View <ArrowRight className="h-3.5 w-3.5" /></span>
        </div>
      </div>
    </Link>
  )
}

function SiteHeader() {
  return (
    <header className="site-header sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link to="/" aria-label="SurePlug home" className="flex shrink-0 items-center gap-3">
          <span className="brand-mark flex h-11 w-11 items-center justify-center rounded-2xl bg-orange-500 text-xl font-black text-white">S</span>
          <span className="block">
            <span className="block text-xl font-black leading-tight tracking-tight text-slate-950">SurePlug</span>
            <span className="hidden text-xs text-slate-500 sm:block">Campus life, plugged in.</span>
          </span>
        </Link>
        <nav aria-label="Main navigation" className="hidden items-center gap-1 md:flex">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/products" className="nav-link">Explore products</Link>
          <Link to="/vendors" className="nav-link">Vendors</Link>
        </nav>
        <Link to="/dashboard" className="inline-flex shrink-0 items-center gap-2 rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-orange-500 sm:px-5">
          <Store className="h-4 w-4" /><span className="hidden sm:inline">Sell on SurePlug</span><span className="sm:hidden">Sell</span>
        </Link>
      </div>
    </header>
  )
}

function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm text-slate-500 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
        <Link to="/" className="flex items-center gap-2 font-bold text-slate-900"><span className="flex h-8 w-8 items-center justify-center rounded-xl bg-orange-500 font-black text-white">S</span> SurePlug</Link>
        <p>Discover products and local sellers around your campus.</p>
        <div className="flex gap-4"><Link className="hover:text-orange-600" to="/products">Browse listings</Link><Link className="hover:text-orange-600" to="/dashboard">Become a seller</Link></div>
      </div>
    </footer>
  )
}

function HomePage() {
  const navigate = useNavigate()
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    fetchJson<Product[]>('/products/?ordering=recent').then((data) => { if (active) setProducts(data) }).catch(() => {
      if (active) setLoadError('We could not load listings right now. You can still browse the marketplace or try again shortly.')
    }).finally(() => { if (active) setLoading(false) })
    fetchJson<Category[]>('/categories/').then((data) => { if (active) setCategories(data) }).catch(() => undefined)
    return () => { active = false }
  }, [reloadKey])

  const recent = useMemo(() => readRecent().map((slug) => products.find((item) => item.slug === slug)).filter((item): item is Product => Boolean(item)).slice(0, 4), [products])

  const filteredProducts = useMemo(() => products.filter((product) => {
    const query = search.trim().toLowerCase()
    const matchesText = !query || product.name.toLowerCase().includes(query) || product.description.toLowerCase().includes(query) || product.vendor?.business_name.toLowerCase().includes(query)
    const matchesCategory = !selectedCategory || product.category?.slug === selectedCategory
    return matchesText && matchesCategory
  }), [products, search, selectedCategory])

  return (
    <div className="home-page text-slate-900">
      <main>
        <section className="hero-section">
          <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[1.08fr_0.92fr] lg:items-center lg:px-8 lg:py-20">
            <div className="relative z-10">
              <h1 className="max-w-2xl text-4xl font-black leading-[1.04] tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">Buy and sell on campus.</h1>
              <p className="mt-5 max-w-xl text-base leading-7 text-slate-600 sm:text-lg">Browse food, fashion, gadgets and essentials from student sellers near you. See the price, message the seller on WhatsApp, and meet on campus.</p>
              <form onSubmit={(event) => { event.preventDefault(); navigate(`/products${search.trim() ? `?search=${encodeURIComponent(search.trim())}` : ''}`) }} className="search-panel mt-8 flex max-w-2xl flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl shadow-slate-900/5 sm:flex-row sm:items-center">
                <div className="flex min-w-0 flex-1 items-center gap-3 px-3 py-2"><Search className="h-5 w-5 shrink-0 text-slate-400" /><input aria-label="Search products" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search food, clothes, phones, books…" className="min-w-0 w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400" /></div>
                <button type="submit" className="inline-flex items-center justify-center gap-2 rounded-xl bg-orange-500 px-6 py-3 text-sm font-bold text-white transition hover:bg-orange-600">Search <ArrowRight className="h-4 w-4" /></button>
              </form>
              <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-slate-500"><span className="inline-flex items-center gap-1.5"><ShieldCheck className="h-4 w-4 text-emerald-600" /> Browse without signing up</span><span className="inline-flex items-center gap-1.5"><MapPin className="h-4 w-4 text-orange-500" /> Meet sellers on campus</span></div>
              {categories.length > 0 && <div className="mt-7 flex flex-wrap gap-2"><span className="mr-1 self-center text-xs font-semibold uppercase tracking-wider text-slate-400">Popular:</span>{categories.slice(0, 5).map((category) => <button key={category.id} onClick={() => { setSelectedCategory(category.slug); document.getElementById('latest-listings')?.scrollIntoView({ behavior: 'smooth' }) }} className={`rounded-full border px-3 py-1.5 text-sm font-medium transition ${selectedCategory === category.slug ? 'border-orange-500 bg-orange-500 text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-orange-300 hover:text-orange-700'}`}>{category.name}</button>)}</div>}
            </div>
            <aside className="fresh-panel hidden lg:block" aria-label="Just listed">
              <div className="fresh-panel-head"><h2 className="text-lg font-bold">Just listed</h2><Link to="/products" className="text-sm font-semibold text-indigo-800">See all</Link></div>
              {loading && products.length === 0 ? <div className="space-y-3 py-2">{[0, 1, 2].map((item) => <div key={item} className="skeleton h-12 rounded-xl" />)}</div> : products.length > 0 ? products.slice(0, 4).map((item) => (
                <Link key={item.id} to={`/product/${item.slug}`} className="fresh-item">
                  <span className="fresh-thumb">{item.image ? <img src={item.image} alt="" loading="lazy" /> : <ShoppingBag className="h-5 w-5" />}</span>
                  <span className="min-w-0 flex-1"><span className="block truncate font-semibold">{item.name}</span><span className="block truncate text-xs text-slate-500">{item.vendor?.business_name || 'Campus seller'}</span></span>
                  <span className="font-bold">{formatCurrency(item.price)}</span>
                </Link>
              )) : <p className="py-4 text-sm text-slate-500">New listings will show up here.</p>}
            </aside>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
          <div className="section-heading"><div><p className="eyebrow">Explore the marketplace</p><h2 className="section-title">What are we finding today?</h2><p className="mt-2 text-sm text-slate-500">The essentials, the nice-to-haves, and that one thing your roommate mentioned.</p></div><Link to="/products" className="section-link">All listings <ArrowRight className="h-4 w-4" /></Link></div>
          {categories.length > 0 ? <div className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">{categories.map((category, index) => <button key={category.id} onClick={() => { setSelectedCategory(category.slug); document.getElementById('latest-listings')?.scrollIntoView({ behavior: 'smooth' }) }} className={`category-tile category-tile-${index % 4} text-left ${selectedCategory === category.slug ? 'category-tile-active' : ''}`}><span className="category-icon"><ShoppingBag className="h-5 w-5" /></span><span className="mt-4 block font-bold text-slate-900">{category.name}</span><span className="mt-1 block text-xs text-slate-500">Explore items <ArrowRight className="ml-1 inline h-3 w-3" /></span></button>)}</div> : <div className="mt-7 rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">Categories will appear here when available.</div>}
        </section>

        {recent.length > 0 && <section className="mx-auto max-w-7xl px-4 pt-10 sm:px-6 lg:px-8"><div className="section-heading"><div><h2 className="section-title">Pick up where you left off</h2><p className="mt-2 text-sm text-slate-500">Listings you looked at recently.</p></div></div><div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{recent.map((item) => <ProductCard key={item.id} product={item} />)}</div></section>}

        <section id="latest-listings" className="mx-auto max-w-7xl scroll-mt-28 px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
          <div className="section-heading"><div><p className="eyebrow">Straight from the campus scene</p><h2 className="section-title">Just listed</h2><p className="mt-2 text-sm text-slate-500">New finds from student vendors and local campus businesses.</p></div><Link to="/products" className="section-link">Browse everything <ArrowRight className="h-4 w-4" /></Link></div>
          {selectedCategory && <div className="mt-5 flex items-center gap-3 text-sm"><span className="rounded-full bg-orange-50 px-3 py-1.5 font-semibold text-orange-700">Filtering: {categories.find((item) => item.slug === selectedCategory)?.name || selectedCategory}</span><button onClick={() => setSelectedCategory('')} className="font-semibold text-slate-500 underline underline-offset-4 hover:text-slate-900">Clear filter</button></div>}
          {loadError && <div className="mt-6"><RetryAlert message={loadError} onRetry={() => { setLoadError(''); setLoading(true); setReloadKey((key) => key + 1) }} /></div>}
          {loading ? <div className="mt-7 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{[0, 1, 2, 3].map((item) => <div key={item} className="overflow-hidden rounded-2xl border border-slate-200 bg-white"><div className="skeleton h-48" /><div className="space-y-3 p-4"><div className="skeleton h-4 w-2/3" /><div className="skeleton h-4 w-full" /><div className="skeleton h-6 w-1/3" /></div></div>)}</div> : filteredProducts.length > 0 ? <div className="mt-7 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{filteredProducts.slice(0, 8).map((product) => <ProductCard key={product.id} product={product} />)}</div> : <div className="empty-state mt-7"><span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-100 text-orange-600"><Search className="h-5 w-5" /></span><h3 className="mt-4 font-bold text-slate-900">No listings to show yet</h3><p className="mx-auto mt-1 max-w-md text-sm text-slate-500">Try another category or browse all listings to see what's available.</p><Link to="/products" className="mt-4 inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white">Explore listings <ArrowRight className="h-4 w-4" /></Link></div>}
        </section>

        <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12"><div className="seller-banner overflow-hidden rounded-[2rem] px-6 py-9 sm:px-10 sm:py-12 lg:px-14"><div className="relative z-10 flex flex-col gap-7 md:flex-row md:items-center md:justify-between"><div className="max-w-2xl"><p className="eyebrow text-orange-200">For campus entrepreneurs</p><h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-4xl">Your hustle deserves more eyes.</h2><p className="mt-3 max-w-xl leading-7 text-slate-300">Put your products in front of more students. Share your prices, show what is available, and let customers reach you directly.</p></div><Link to="/dashboard" className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full bg-orange-500 px-6 py-3.5 font-bold text-white transition hover:bg-orange-400">Start selling <ArrowRight className="h-4 w-4" /></Link></div></div></section>
      </main>
    </div>
  )
}

function ProductListingPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [campuses, setCampuses] = useState<Campus[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [searchParams] = useSearchParams()
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [category, setCategory] = useState('')
  const [campus, setCampus] = useState('')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [loadError, setLoadError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [sort, setSort] = useState('recent')

  useEffect(() => {
    Promise.all([
      fetchJson<Product[]>(`/products/?ordering=recent`),
      fetchJson<Category[]>(`/categories/`),
      fetchJson<Campus[]>(`/campuses/`),
    ]).then(([productData, categoryData, campusData]) => {
      setProducts(productData)
      setCategories(categoryData)
      setCampuses(campusData)
      setLoading(false)
    }).catch((error: Error) => {
      setProducts([])
      setLoadError(error.message)
      setLoading(false)
    })
  }, [reloadKey])

  const filteredProducts = useMemo(() => {
    return products.filter((item) => {
      const matchesSearch = !search || item.name.toLowerCase().includes(search.toLowerCase()) || item.description.toLowerCase().includes(search.toLowerCase())
      const matchesCategory = !category || item.category?.slug === category
      const matchesCampus = !campus || item.campus?.name === campus || item.vendor?.campus_name === campus
      const matchesMin = !minPrice || Number(item.price) >= Number(minPrice)
      const matchesMax = !maxPrice || Number(item.price) <= Number(maxPrice)
      return matchesSearch && matchesCategory && matchesCampus && matchesMin && matchesMax
    })
  }, [products, search, category, campus, minPrice, maxPrice])

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="page-hero mb-8 p-6 sm:p-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="eyebrow">Product discovery</div>
            <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">Find your next good find.</h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">Search campus listings, compare prices, and connect with sellers directly.</p>
          </div>
          <div className="flex w-full max-w-xl items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
            <Search className="h-5 w-5 text-slate-400" />
            <input aria-label="Search products or vendors" value={search} onChange={(e) => setSearch(e.target.value)} className="w-full border-0 bg-transparent outline-none" placeholder="Search products or vendors" />
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex items-center justify-between gap-3"><div className="text-lg font-bold">Filters</div><button type="button" className="filters-toggle ml-auto mr-3 text-sm font-bold lg:hidden" aria-expanded={filtersOpen} onClick={() => setFiltersOpen((open) => !open)}>{filtersOpen ? 'Hide' : 'Show'}</button><button type="button" onClick={() => { setCategory(''); setCampus(''); setMinPrice(''); setMaxPrice(''); setSearch('') }} className="text-xs font-semibold text-orange-700 hover:text-orange-800">Clear all</button></div>
          <div className={`space-y-5 ${filtersOpen ? '' : 'hidden'} lg:block`}>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Category</span>
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                <option value="">All categories</option>
                {categories.map((item) => <option key={item.id} value={item.slug}>{item.name}</option>)}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Campus zone</span>
              <select value={campus} onChange={(e) => setCampus(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                <option value="">All zones</option>
                {campuses.map((item) => <option key={item.id} value={item.name}>{item.name}</option>)}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label>
                <span className="mb-2 block text-sm font-medium text-slate-700">Min price</span>
                <input value={minPrice} onChange={(e) => setMinPrice(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2" placeholder="₦0" />
              </label>
              <label>
                <span className="mb-2 block text-sm font-medium text-slate-700">Max price</span>
                <input value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2" placeholder="₦50000" />
              </label>
            </div>
          </div>
        </aside>

        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3 text-sm text-slate-500"><span>{loading ? 'Loading listings…' : `${filteredProducts.length} ${filteredProducts.length === 1 ? 'listing' : 'listings'} found`}</span><label className="sort-control"><span className="sr-only">Sort listings</span><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="recent">Newest first</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option></select></label>{(search || category || campus || minPrice || maxPrice) && <button onClick={() => { setCategory(''); setCampus(''); setMinPrice(''); setMaxPrice(''); setSearch('') }} className="font-semibold text-orange-700 hover:text-orange-800">Reset filters</button>}</div>
          {loadError && <RetryAlert message={`We couldn't load listings. ${loadError}`} onRetry={() => { setLoadError(''); setLoading(true); setReloadKey((key) => key + 1) }} />}
          {loading ? <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">{[0, 1, 2].map((item) => <div key={item} className="overflow-hidden rounded-2xl border border-slate-200 bg-white"><div className="skeleton h-48" /><div className="space-y-3 p-4"><div className="skeleton h-4 w-2/3" /><div className="skeleton h-4 w-full" /><div className="skeleton h-6 w-1/3" /></div></div>)}</div> : filteredProducts.length === 0 ? <div className="empty-state"><span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-100 text-orange-600"><Search className="h-5 w-5" /></span><h2 className="mt-4 font-bold text-slate-900">No matching listings</h2><p className="mt-1 text-sm text-slate-500">Try a different search or clear one or more filters.</p><button onClick={() => { setCategory(''); setCampus(''); setMinPrice(''); setMaxPrice(''); setSearch('') }} className="mt-4 rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white">Clear filters</button></div> : (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {[...filteredProducts].sort((a, b) => sort === 'price_asc' ? Number(a.price) - Number(b.price) : sort === 'price_desc' ? Number(b.price) - Number(a.price) : 0).map((product) => <ProductCard key={product.id} product={product} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ProductDetailPage() {
  const { slug } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!slug) return
    setLoading(true)
    setLoadError('')
    fetchJson<Product>(`/products/${slug}/`).then((data) => { setProduct(data); rememberProduct(data.slug) }).catch((error: Error) => {
      setProduct(null)
      setLoadError(error.message)
    }).finally(() => setLoading(false))
  }, [slug])

  if (loading) return <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"><div className="skeleton h-8 w-48 rounded-lg" /><div className="mt-6 grid gap-8 lg:grid-cols-2"><div className="skeleton min-h-[360px] rounded-3xl" /><div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6"><div className="skeleton h-5 w-1/3 rounded" /><div className="skeleton h-8 w-4/5 rounded" /><div className="skeleton h-10 w-1/2 rounded" /><div className="skeleton h-24 w-full rounded" /></div></div></div>
  if (!product) return <div className="mx-auto max-w-4xl px-4 py-16 text-center sm:px-6"><div role="alert" className="rounded-3xl border border-red-200 bg-white p-8"><h1 className="text-2xl font-black text-slate-900">We couldn't find that listing</h1><p className="mt-2 text-sm text-slate-600">{loadError || 'This product is not available.'}</p><Link to="/products" className="mt-5 inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">Browse other products</Link></div></div>

  const contactMessage = encodeURIComponent(`Hi ${product.vendor?.business_name}, I'm interested in ${product.name}. Can you confirm the price and availability?`)
  const phone = (product.contact_phone || product.vendor?.phone || '').trim()
  const whatsappNumber = toWhatsAppNumber(product.whatsapp_number || phone)
  const whatsappLink = `https://wa.me/${whatsappNumber}?text=${contactMessage}`

  return (
    <div className="mx-auto max-w-6xl px-4 pb-32 pt-4 sm:px-6 lg:pb-12 lg:pt-6">
      <Link to="/products" className="back-link"><ArrowLeft className="h-4 w-4" /> All listings</Link>
      <div className="h-2" />
      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          {product.image ? <img src={product.image} alt={product.name} className="h-[420px] w-full rounded-3xl object-cover shadow-lg" /> : <ImagePlaceholder className="h-[420px] w-full rounded-3xl" />}
          <div className="mt-4 grid grid-cols-3 gap-3">
            {(product.gallery || []).slice(0, 3).map((image) => (
              <img key={image.id} src={image.image} alt={product.name} className="h-28 w-full rounded-2xl object-cover" />
            ))}
          </div>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="rounded-full bg-orange-100 px-2.5 py-1 text-xs font-semibold text-orange-700">{product.category?.name || 'General'}</span>
            <span className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700"><Tag className="h-3.5 w-3.5" /> <span className="capitalize">{product.condition}</span></span>
          </div>
          <h1 className="mt-4 text-3xl font-black text-slate-900">{product.name}</h1>
          <div className="mt-3 text-4xl font-black text-slate-900">{formatCurrency(product.price)}</div>
          <div className="mt-2 text-sm text-slate-500">Last price update: {new Date(product.price_updated_at).toLocaleDateString()}</div>
          <div className="mt-5 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">{product.description}</div>
          <div className="contact-actions mt-6 grid gap-3">
            {whatsappNumber && <a href={whatsappLink} target="_blank" rel="noreferrer" className="flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 font-semibold text-white"><MessageCircle className="h-4 w-4" /> WhatsApp</a>}
            {phone && <a href={`tel:${phone}`} className="flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-3 font-semibold text-slate-900"><Phone className="h-4 w-4" /> Call seller</a>}
            {!whatsappNumber && !phone && <p className="rounded-xl bg-slate-100 p-3 text-center text-sm text-slate-600">This seller hasn't added contact details yet.</p>}
          </div>
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-100 font-bold text-orange-700">{product.vendor?.business_name?.slice(0, 1) || 'V'}</div>
                <div>
                  <div className="font-bold text-slate-900">{product.vendor?.business_name}</div>
                  <div className="text-xs text-slate-500">{product.vendor?.campus_name}</div>
                </div>
              </div>
              {product.vendor?.is_verified && <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700"><ShieldCheck className="h-3.5 w-3.5" /> Verified</span>}
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm text-slate-600"><MapPin className="h-4 w-4" /> {product.vendor?.location_description || 'Campus neighbourhood'}</div>
          </div>
          <p className="safety-tip mt-4 flex gap-2 text-xs leading-5"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />Meet in a public spot on campus, check the item, then pay. Never send money before you see it.</p>
        </div>
      </div>
    </div>
  )
}

function VendorPage() {
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    fetchJson<Vendor[]>('/vendors/').then(setVendors).catch((error: Error) => setLoadError(error.message)).finally(() => setLoading(false))
  }, [reloadKey])

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
      <div className="page-hero mb-8 px-6 py-8 sm:px-9 sm:py-10">
        <p className="eyebrow">Meet the people behind the products</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Campus vendors</h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">Explore local storefronts, discover what they offer, and connect with sellers directly.</p>
      </div>
      {loadError && <div className="mb-5"><RetryAlert message={`We couldn't load vendors. ${loadError}`} onRetry={() => { setLoadError(''); setLoading(true); setReloadKey((key) => key + 1) }} /></div>}
      {loading ? <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">{[0, 1, 2].map((item) => <div key={item} className="rounded-3xl border border-slate-200 bg-white p-5"><div className="skeleton h-16 w-16 rounded-2xl" /><div className="skeleton mt-4 h-5 w-2/3" /><div className="skeleton mt-3 h-4 w-full" /><div className="skeleton mt-2 h-4 w-4/5" /></div>)}</div> : vendors.length ? <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {vendors.map((vendor) => (
          <article key={vendor.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-orange-200 hover:shadow-lg">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-orange-100 text-2xl font-black text-orange-700">{vendor.business_name.slice(0, 1)}</div>
              <div className="min-w-0"><div className="truncate text-xl font-bold text-slate-900">{vendor.business_name}</div><div className="mt-1 text-sm text-slate-500">{vendor.campus_name || 'Campus seller'}</div>{vendor.is_verified && <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-emerald-700"><ShieldCheck className="h-3.5 w-3.5" /> Verified seller</span>}</div>
            </div>
            <p className="mt-4 line-clamp-3 min-h-[4.5rem] text-sm leading-6 text-slate-600">{vendor.description || 'A local campus seller with products and services for students.'}</p>
            <div className="mt-4 flex items-center gap-2 text-sm text-slate-500"><MapPin className="h-4 w-4 text-orange-500" /> {vendor.location_description || 'Near campus'}</div>
            <Link to={`/vendor/${vendor.slug}`} className="mt-5 inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-orange-500">View storefront <ArrowRight className="h-4 w-4" /></Link>
          </article>
        ))}
      </div> : <div className="empty-state"><span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-100 text-orange-600"><Store className="h-5 w-5" /></span><h2 className="mt-4 font-bold text-slate-900">No storefronts available yet</h2><p className="mt-1 text-sm text-slate-500">Vendor profiles will appear here as sellers join SurePlug.</p><Link to="/dashboard" className="mt-4 inline-flex rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white">Become a seller</Link></div>}
    </div>
  )
}

function VendorStorefrontPage() {
  const { slug } = useParams()
  const [vendor, setVendor] = useState<Vendor | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!slug) return
    setLoading(true)
    setLoadError('')
    fetchJson<{ vendor: Vendor; products: Product[] }>(`/vendors/${slug}/`).then((data) => {
      setVendor(data.vendor)
      setProducts(data.products)
    }).catch((error: Error) => {
      setVendor(null)
      setProducts([])
      setLoadError(error.message)
    }).finally(() => {
      setLoading(false)
    })
  }, [slug])

  if (loading) return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8"><div className="skeleton h-36 rounded-3xl" /><div className="mt-8 grid gap-5 md:grid-cols-3">{[0, 1, 2].map((item) => <div key={item} className="skeleton h-72 rounded-2xl" />)}</div></div>
  if (!vendor) return <div className="mx-auto max-w-4xl px-4 py-16 text-center sm:px-6"><div role="alert" className="rounded-3xl border border-red-200 bg-white p-8"><h1 className="text-2xl font-black text-slate-900">Storefront unavailable</h1><p className="mt-2 text-sm text-slate-600">{loadError || 'This vendor is not available.'}</p><Link to="/vendors" className="mt-5 inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">Browse vendors</Link></div></div>

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-orange-100 text-3xl font-black text-orange-700">{vendor.business_name.slice(0, 1)}</div>
            <div>
              <h1 className="text-3xl font-black text-slate-900">{vendor.business_name}</h1>
              <div className="mt-1 text-sm text-slate-500">{vendor.campus_name} • {vendor.location_description || 'Campus neighbourhood'}</div>
            </div>
          </div>
          {vendor.is_verified && <span className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-2 text-sm font-medium text-emerald-700"><ShieldCheck className="h-4 w-4" /> Verified seller</span>}
        </div>
        <p className="mt-5 max-w-3xl text-slate-600">{vendor.description}</p>
      </div>
      {products.length ? <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div> : <div className="empty-state mt-8"><span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-100 text-orange-600"><ShoppingBag className="h-5 w-5" /></span><h2 className="mt-4 font-bold text-slate-900">No products listed yet</h2><p className="mt-1 text-sm text-slate-500">This seller's products will appear here when they are available.</p><Link to="/products" className="mt-4 inline-flex rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white">Browse all listings</Link></div>}
    </div>
  )
}

function DashboardPage() {
  const [profile, setProfile] = useState<VendorDashboard | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [campuses, setCampuses] = useState<Campus[]>([])
  const [loading, setLoading] = useState(true)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [credentials, setCredentials] = useState<Record<string, string>>({})
  const [newListing, setNewListing] = useState({
    name: '',
    description: '',
    category: '',
    campus: '',
    price: '',
    condition: 'new',
    availability: 'in_stock',
  })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let active = true
    fetchJson<VendorDashboard>('/vendors/dashboard/').then((data) => {
      if (active) setProfile(data)
    }).catch((requestError: Error) => {
      const notSignedIn = requestError instanceof ApiError && [401, 403].includes(requestError.status)
      if (active && !notSignedIn) setError(requestError.message)
    }).finally(() => {
      if (active) setLoading(false)
    })
    fetchJson<Category[]>('/categories/').then((data) => {
      if (active) setCategories(data)
    }).catch((requestError: Error) => {
      if (active) setError(requestError.message)
    })
    fetchJson<Campus[]>('/campuses/').then((data) => {
      if (active) setCampuses(data)
    }).catch((requestError: Error) => {
      if (active) setError(requestError.message)
    })
    return () => { active = false }
  }, [])

  const refreshDashboard = async () => {
    const data = await fetchJson<VendorDashboard>('/vendors/dashboard/')
    setProfile(data)
  }

  const submitAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    try {
      const isRegistering = authMode === 'register'
      await fetchJson('/auth/csrf/')
      const response = await fetchJson<{ message: string }>('/auth/' + (isRegistering ? 'register/' : 'login/'), {
        method: 'POST',
        body: JSON.stringify(isRegistering ? credentials : {
          username: credentials.username,
          password: credentials.password,
        }),
      })
      await refreshDashboard()
      setNotice(response.message)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  const submitListing = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    try {
      const response = await fetchJson<{ message: string }>('/products/create/', {
        method: 'POST',
        body: JSON.stringify(newListing),
      })
      await refreshDashboard()
      setNewListing({
        name: '',
        description: '',
        category: '',
        campus: '',
        price: '',
        condition: 'new',
        availability: 'in_stock',
      })
      setNotice(response.message)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not create listing.')
    } finally {
      setSubmitting(false)
    }
  }

  const togglePublished = async (product: Product) => {
    setError('')
    setNotice('')
    try {
      await fetchJson(`/products/${product.slug}/update/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_published: !product.is_published }),
      })
      await refreshDashboard()
      setNotice('Listing visibility updated.')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not update listing.')
    }
  }

  const deleteProduct = async (product: Product) => {
    setError('')
    setNotice('')
    try {
      await fetchJson(`/products/${product.slug}/delete/`, { method: 'DELETE' })
      await refreshDashboard()
      setNotice('Listing deleted.')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not delete listing.')
    }
  }

  const fieldClass = 'w-full rounded-xl border border-slate-200 bg-white px-3 py-2'

  if (loading) return <div className="mx-auto max-w-6xl px-6 py-10">Loading vendor dashboard...</div>

  if (!profile) {
    return (
      <div className="mx-auto max-w-xl px-6 py-10">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-3xl font-black text-slate-900">Vendor dashboard</h1>
          <p className="mt-2 text-slate-600">Sign in to manage your listings, or create a vendor account to get started.</p>
          {error && <div role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</div>}
          {notice && <div role="status" className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</div>}
          <div className="mt-6 flex gap-3">
            <button type="button" onClick={() => { setAuthMode('login'); setError('') }} className={`rounded-full px-4 py-2 text-sm font-medium ${authMode === 'login' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'}`}>Sign in</button>
            <button type="button" onClick={() => { setAuthMode('register'); setError('') }} className={`rounded-full px-4 py-2 text-sm font-medium ${authMode === 'register' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'}`}>Create vendor account</button>
          </div>
          <form onSubmit={submitAuth} className="mt-5 space-y-4">
            <label className="block text-sm font-medium text-slate-700">Username
              <input required autoComplete="username" value={credentials.username || ''} onChange={(event) => setCredentials((current) => ({ ...current, username: event.target.value }))} className={`${fieldClass} mt-1`} />
            </label>
            {authMode === 'register' && <>
              <label className="block text-sm font-medium text-slate-700">Email
                <input type="email" autoComplete="email" value={credentials.email || ''} onChange={(event) => setCredentials((current) => ({ ...current, email: event.target.value }))} className={`${fieldClass} mt-1`} />
              </label>
              <label className="block text-sm font-medium text-slate-700">Business name
                <input required value={credentials.business_name || ''} onChange={(event) => setCredentials((current) => ({ ...current, business_name: event.target.value }))} className={`${fieldClass} mt-1`} />
              </label>
              <label className="block text-sm font-medium text-slate-700">Phone
                <input value={credentials.phone || ''} onChange={(event) => setCredentials((current) => ({ ...current, phone: event.target.value }))} className={`${fieldClass} mt-1`} />
              </label>
              <label className="block text-sm font-medium text-slate-700">Campus
                <select value={credentials.campus || ''} onChange={(event) => setCredentials((current) => ({ ...current, campus: event.target.value }))} className={`${fieldClass} mt-1`}>
                  <option value="">Choose a campus (optional)</option>
                  {campuses.map((campus) => <option key={campus.id} value={campus.name}>{campus.name}</option>)}
                </select>
              </label>
            </>}
            <label className="block text-sm font-medium text-slate-700">Password
              <input required type="password" minLength={8} autoComplete={authMode === 'login' ? 'current-password' : 'new-password'} value={credentials.password || ''} onChange={(event) => setCredentials((current) => ({ ...current, password: event.target.value }))} className={`${fieldClass} mt-1`} />
            </label>
            <button disabled={submitting} className="w-full rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white disabled:opacity-60">{submitting ? 'Please wait...' : authMode === 'login' ? 'Sign in' : 'Create account'}</button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-black text-slate-900">{profile.vendor.business_name}</h1>
            <p className="mt-1 text-sm text-slate-500">Vendor dashboard</p>
          </div>
          <button onClick={async () => {
            try {
              await fetchJson('/auth/logout/', { method: 'POST', body: JSON.stringify({}) })
              setProfile(null)
              setNotice('You have signed out.')
            } catch (requestError) {
              setError(requestError instanceof Error ? requestError.message : 'Could not sign out.')
            }
          }} className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700">Sign out</button>
        </div>
        <p className="mt-2 text-slate-600">Manage listings, stock visibility, and contact information from one place.</p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl bg-orange-50 p-4"><div className="text-sm text-slate-600">Published</div><div className="mt-2 text-3xl font-black text-orange-600">{profile.stats.published}</div></div>
          <div className="rounded-2xl bg-slate-100 p-4"><div className="text-sm text-slate-600">Unavailable</div><div className="mt-2 text-3xl font-black text-slate-700">{profile.stats.unavailable}</div></div>
          <div className="rounded-2xl bg-emerald-50 p-4"><div className="text-sm text-slate-600">Drafts</div><div className="mt-2 text-3xl font-black text-emerald-600">{profile.stats.drafts}</div></div>
        </div>
        {error && <div role="alert" className="mt-6 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        {notice && <div role="status" className="mt-6 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</div>}
        <form onSubmit={submitListing} className="mt-8 rounded-2xl bg-slate-50 p-5">
          <h2 className="text-xl font-bold text-slate-900">Add a listing</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">Product name
              <input required maxLength={200} value={newListing.name} onChange={(event) => setNewListing((current) => ({ ...current, name: event.target.value }))} className={`${fieldClass} mt-1`} />
            </label>
            <label className="text-sm font-medium text-slate-700">Price (NGN)
              <input required type="number" min="0" step="0.01" value={newListing.price} onChange={(event) => setNewListing((current) => ({ ...current, price: event.target.value }))} className={`${fieldClass} mt-1`} />
            </label>
            <label className="text-sm font-medium text-slate-700">Category
              <select required value={newListing.category} onChange={(event) => setNewListing((current) => ({ ...current, category: event.target.value }))} className={`${fieldClass} mt-1`}>
                <option value="">Choose a category</option>
                {categories.map((category) => <option key={category.id} value={category.name}>{category.name}</option>)}
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">Campus
              <select required value={newListing.campus} onChange={(event) => setNewListing((current) => ({ ...current, campus: event.target.value }))} className={`${fieldClass} mt-1`}>
                <option value="">Choose a campus</option>
                {campuses.map((campus) => <option key={campus.id} value={campus.name}>{campus.name}</option>)}
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700 md:col-span-2">Description
              <textarea required value={newListing.description} onChange={(event) => setNewListing((current) => ({ ...current, description: event.target.value }))} className={`${fieldClass} mt-1`} rows={3} />
            </label>
          </div>
          <button disabled={submitting} className="mt-4 rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white disabled:opacity-60">{submitting ? 'Saving...' : 'Publish listing'}</button>
        </form>
        <div className="mt-8">
          <h2 className="text-xl font-bold text-slate-900">Your listings</h2>
          <div className="mt-4 space-y-3">
            {profile.products.map((product) => (
              <div key={product.id} className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 p-4">
                <div>
                  <Link to={`/product/${product.slug}`} className="font-semibold text-slate-900 hover:text-orange-600">{product.name}</Link>
                  <div className="mt-1 text-sm text-slate-500">{formatCurrency(product.price)} · {product.availability}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => void togglePublished(product)} className="rounded-full border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700">{product.is_published ? 'Unpublish' : 'Publish'}</button>
                  <button onClick={() => void deleteProduct(product)} className="rounded-full border border-red-200 px-3 py-2 text-sm font-medium text-red-700">Delete</button>
                </div>
              </div>
            ))}
            {profile.products.length === 0 && <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">No listings yet. Add your first product above.</p>}
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell min-h-screen">
        <ScrollToTop />
        <SiteHeader />
        <div className="route-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductListingPage />} />
            <Route path="/product/:slug" element={<ProductDetailPage />} />
            <Route path="/vendors" element={<VendorPage />} />
            <Route path="/vendor/:slug" element={<VendorStorefrontPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </div>
        <SiteFooter />
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}

export default App
