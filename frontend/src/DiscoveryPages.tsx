import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { LocateFixed, MapPin, Radio, Send, ShieldCheck } from 'lucide-react'

const API_BASE = 'https://sureplug-0q7j.onrender.com/api/v1'

function csrfToken() {
  const cookie = document.cookie.split('; ').find((item) => item.startsWith('csrftoken='))
  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : ''
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body) headers.set('Content-Type', 'application/json')
  if (options.method && options.method !== 'GET') {
    const token = csrfToken()
    if (token) headers.set('X-CSRFToken', token)
  }
  const response = await fetch(API_BASE + path, { ...options, headers, credentials: 'include' })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(typeof data.error === 'string' ? data.error : 'Request failed. Sign in and try again.')
  return data as T
}

type NearbyVendor = { id: number; slug: string; business_name: string; campus_name?: string; location_label?: string; distance_km: number; is_verified?: boolean }
type NearbyProduct = { id: number; slug: string; name: string; price: string; image?: string | null; distance_km: number; vendor?: { business_name: string } }
type Signal = { id: number; item_name: string; category_name?: string; description: string; budget_min?: string | null; budget_max?: string | null; location_label: string; radius_km: number; urgency: string; status: string; expires_at: string; response_count?: number }
type Category = { id: number; name: string; slug: string }

const money = (value?: string | null) => value ? '₦' + Number(value).toLocaleString() : 'No fixed budget'

export function NearbyPage() {
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [radius, setRadius] = useState('5')
  const [vendors, setVendors] = useState<NearbyVendor[]>([])
  const [products, setProducts] = useState<NearbyProduct[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  const locate = () => {
    setError('')
    if (!navigator.geolocation) { setError('This browser does not support location. Enter coordinates manually.'); return }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => { setLatitude(String(coords.latitude)); setLongitude(String(coords.longitude)) },
      () => setError('Location access was unavailable. Allow location permission or enter coordinates manually.'),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    )
  }

  const search = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true); setError(''); setSearched(true)
    try {
      const result = await api<{ vendors: NearbyVendor[]; products: NearbyProduct[] }>(`/nearby/?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}&radius_km=${radius}`)
      setVendors(result.vendors); setProducts(result.products)
    } catch (err) { setError(err instanceof Error ? err.message : 'Nearby search failed.') }
    finally { setLoading(false) }
  }

  return <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
    <div className="page-hero p-6 sm:p-9">
      <p className="eyebrow">Location-aware marketplace</p>
      <h1 className="mt-2 text-3xl font-black sm:text-4xl">Find what is close to you.</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Discover nearby sellers and available listings around your current location or a place you choose.</p>
      <form onSubmit={search} className="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-[1fr_1fr_160px_auto]">
        <label className="text-sm font-semibold">Latitude<input required type="number" step="any" min="-90" max="90" value={latitude} onChange={e=>setLatitude(e.target.value)} placeholder="e.g. 9.203" className="mt-1 w-full rounded-xl border p-3 font-normal" /></label>
        <label className="text-sm font-semibold">Longitude<input required type="number" step="any" min="-180" max="180" value={longitude} onChange={e=>setLongitude(e.target.value)} placeholder="e.g. 12.481" className="mt-1 w-full rounded-xl border p-3 font-normal" /></label>
        <label className="text-sm font-semibold">Search radius<select value={radius} onChange={e=>setRadius(e.target.value)} className="mt-1 w-full rounded-xl border bg-white p-3 font-normal"><option value="1">1 km</option><option value="3">3 km</option><option value="5">5 km</option><option value="10">10 km</option><option value="20">20 km</option><option value="50">50 km</option></select></label>
        <button type="button" onClick={locate} className="self-end rounded-xl border px-4 py-3 text-sm font-bold"><LocateFixed className="mr-2 inline h-4 w-4" />Use my location</button>
        <button disabled={loading} className="rounded-xl bg-slate-950 px-5 py-3 font-bold text-white md:col-span-4">{loading ? 'Searching…' : 'Find nearby'}</button>
      </form>
      <p className="mt-3 flex items-start gap-2 text-xs text-slate-500"><ShieldCheck className="h-4 w-4 shrink-0" />Your device coordinates are used for this search only. They are not displayed to other users or saved by this search.</p>
    </div>
    {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
    {searched && !loading && !error && <div className="mt-8 space-y-10">
      <section><h2 className="text-2xl font-black">Nearby products</h2>{products.length ? <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{products.map(item=><Link key={item.id} to={`/product/${item.slug}`} className="rounded-2xl border bg-white p-4 hover:shadow-md">{item.image && <img src={item.image} alt="" className="mb-3 h-36 w-full rounded-xl object-cover" />}<h3 className="font-bold">{item.name}</h3><p className="mt-1 font-black">₦{Number(item.price).toLocaleString()}</p><p className="mt-2 text-xs text-slate-500">{item.vendor?.business_name} · {item.distance_km} km away</p></Link>)}</div> : <p className="mt-3 text-sm text-slate-500">No active listings found within this radius.</p>}</section>
      <section><h2 className="text-2xl font-black">Nearby sellers</h2>{vendors.length ? <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{vendors.map(item=><Link key={item.id} to={`/vendor/${item.slug}`} className="rounded-2xl border bg-white p-5 hover:shadow-md"><h3 className="font-bold">{item.business_name}</h3><p className="mt-1 text-sm text-slate-500">{item.location_label || item.campus_name || 'Local seller'}</p><p className="mt-3 text-sm font-semibold">{item.distance_km} km away {item.is_verified ? '· Verified' : ''}</p></Link>)}</div> : <p className="mt-3 text-sm text-slate-500">No sellers with a saved location found within this radius.</p>}</section>
    </div>}
  </main>
}

export function BuyerSignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [form, setForm] = useState({ item_name: '', category: '', description: '', budget_min: '', budget_max: '', location_label: '', radius_km: '5', urgency: 'normal', expiry_hours: '72' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [message, setMessage] = useState<Record<number, string>>({})
  const [prices, setPrices] = useState<Record<number, string>>({})

  const refresh = () => api<Signal[]>('/buyer-signals/').then(setSignals).catch(err=>setError(err instanceof Error ? err.message : 'Sign in to view buyer signals.')).finally(()=>setLoading(false))
  useEffect(() => { refresh(); api<Category[]>('/categories/').then(setCategories).catch(()=>undefined) }, [])

  const createSignal = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setNotice('')
    try {
      await api('/buyer-signals/', { method: 'POST', body: JSON.stringify({ ...form, category: form.category || null, budget_min: form.budget_min || null, budget_max: form.budget_max || null, radius_km: Number(form.radius_km), expiry_hours: Number(form.expiry_hours) }) })
      setNotice('Your request is now visible to relevant sellers.')
      setForm({ item_name: '', category: '', description: '', budget_min: '', budget_max: '', location_label: '', radius_km: '5', urgency: 'normal', expiry_hours: '72' })
      await refresh()
    } catch(err) { setError(err instanceof Error ? err.message : 'Could not publish your request.') }
  }

  const updateSignal = async (signal: Signal, status: string) => {
    try { await api(`/buyer-signals/${signal.id}/`, { method: 'PATCH', body: JSON.stringify({ status }) }); await refresh(); setNotice('Request updated.') }
    catch(err) { setError(err instanceof Error ? err.message : 'Could not update request.') }
  }

  const respond = async (signal: Signal) => {
    try {
      await api(`/buyer-signals/${signal.id}/respond/`, { method: 'POST', body: JSON.stringify({ message: message[signal.id] || 'I can help with this request.', price: prices[signal.id] || null }) })
      setNotice('Your response has been sent to the buyer.')
    } catch(err) { setError(err instanceof Error ? err.message : 'Could not send response.') }
  }

  const field = 'mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5'
  return <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
    <div className="page-hero p-6 sm:p-9"><p className="eyebrow">Buyer demand radar</p><h1 className="mt-2 text-3xl font-black sm:text-4xl">Post what you need. Let sellers find you.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Create a request for an item or service that is hard to find. Matching sellers can respond with availability and a price.</p></div>
    {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
    {notice && <p role="status" className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{notice}</p>}
    <div className="mt-8 grid gap-8 lg:grid-cols-[.9fr_1.1fr]">
      <form onSubmit={createSignal} className="h-fit rounded-3xl border bg-white p-5 shadow-sm sm:p-6">
        <h2 className="text-xl font-black">What are you looking for?</h2>
        <label className="mt-4 block text-sm font-semibold">Item or service<input required maxLength={180} value={form.item_name} onChange={e=>setForm({...form,item_name:e.target.value})} className={field} placeholder="e.g. Used HP laptop" /></label>
        <label className="mt-4 block text-sm font-semibold">Category<select value={form.category} onChange={e=>setForm({...form,category:e.target.value})} className={field}><option value="">Any category</option>{categories.map(c=><option key={c.id} value={String(c.id)}>{c.name}</option>)}</select></label>
        <label className="mt-4 block text-sm font-semibold">Details<textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} className={field} rows={3} placeholder="Describe what you need, preferred condition or specifications." /></label>
        <div className="mt-4 grid grid-cols-2 gap-3"><label className="text-sm font-semibold">Min budget (₦)<input type="number" min="0" value={form.budget_min} onChange={e=>setForm({...form,budget_min:e.target.value})} className={field} /></label><label className="text-sm font-semibold">Max budget (₦)<input type="number" min="0" value={form.budget_max} onChange={e=>setForm({...form,budget_max:e.target.value})} className={field} /></label></div>
        <label className="mt-4 block text-sm font-semibold">Your general area<input required value={form.location_label} onChange={e=>setForm({...form,location_label:e.target.value})} className={field} placeholder="e.g. MAU, Yola" /></label>
        <div className="mt-4 grid grid-cols-2 gap-3"><label className="text-sm font-semibold">Search radius<select value={form.radius_km} onChange={e=>setForm({...form,radius_km:e.target.value})} className={field}><option value="1">1 km</option><option value="3">3 km</option><option value="5">5 km</option><option value="10">10 km</option><option value="20">20 km</option></select></label><label className="text-sm font-semibold">Urgency<select value={form.urgency} onChange={e=>setForm({...form,urgency:e.target.value})} className={field}><option value="low">Whenever</option><option value="normal">Soon</option><option value="urgent">Urgent</option></select></label></div>
        <label className="mt-4 block text-sm font-semibold">Keep request active<select value={form.expiry_hours} onChange={e=>setForm({...form,expiry_hours:e.target.value})} className={field}><option value="24">24 hours</option><option value="72">3 days</option><option value="168">7 days</option></select></label>
        <button className="mt-5 w-full rounded-xl bg-slate-950 px-5 py-3 font-bold text-white"><Radio className="mr-2 inline h-4 w-4" />Broadcast my request</button>
        <p className="mt-3 text-xs text-slate-500">Your precise location is optional. The general area you enter is shown to sellers.</p>
      </form>
      <section><div className="flex items-center justify-between gap-3"><div><h2 className="text-xl font-black">Requests and seller responses</h2><p className="mt-1 text-sm text-slate-500">Your active requests, or requests matching your seller area.</p></div><button onClick={()=>{setLoading(true);refresh()}} className="rounded-full border px-3 py-2 text-xs font-bold">Refresh</button></div>
        {loading ? <p className="mt-5 text-sm text-slate-500">Loading requests…</p> : signals.length ? <div className="mt-4 space-y-4">{signals.map(signal=><article key={signal.id} className="rounded-2xl border bg-white p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-lg font-bold">{signal.item_name}</h3><p className="mt-1 text-xs text-slate-500">{signal.category_name || 'Any category'} · {signal.location_label} · {signal.radius_km} km</p></div><span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold capitalize">{signal.urgency}</span></div><p className="mt-3 text-sm text-slate-600">{signal.description}</p><p className="mt-3 text-sm font-semibold">{money(signal.budget_min)} – {money(signal.budget_max)}</p><p className="mt-2 text-xs text-slate-400">{signal.response_count || 0} seller responses · expires {new Date(signal.expires_at).toLocaleDateString()}</p>
          {signal.status === 'broadcast' && <div className="mt-4 flex flex-wrap gap-2"><button onClick={()=>updateSignal(signal,'paused')} className="rounded-full border px-3 py-2 text-xs font-bold">Pause</button><button onClick={()=>updateSignal(signal,'fulfilled')} className="rounded-full border px-3 py-2 text-xs font-bold">Mark fulfilled</button><button onClick={()=>updateSignal(signal,'closed')} className="rounded-full border px-3 py-2 text-xs font-bold">Close</button></div>}
          <div className="mt-4 grid gap-2 sm:grid-cols-[1fr_140px_auto]"><input value={message[signal.id] || ''} onChange={e=>setMessage({...message,[signal.id]:e.target.value})} placeholder="Message the buyer" className="rounded-xl border px-3 py-2 text-sm" /><input type="number" min="0" value={prices[signal.id] || ''} onChange={e=>setPrices({...prices,[signal.id]:e.target.value})} placeholder="Your price (₦)" className="rounded-xl border px-3 py-2 text-sm" /><button onClick={()=>respond(signal)} className="rounded-xl bg-indigo-950 px-3 py-2 text-sm font-bold text-white"><Send className="mr-1 inline h-4 w-4" />Respond</button></div>
        </article>)}</div> : <div className="empty-state mt-4"><h3 className="font-bold">No requests to show</h3><p className="mt-1 text-sm text-slate-500">Sign in to publish your own request, or check back when buyers post something you can supply.</p><Link to="/dashboard" className="mt-3 inline-flex font-bold underline">Sign in</Link></div>}
      </section>
    </div>
  </main>
}

export function SellerLocationPage() {
  const [form, setForm] = useState({ latitude: '', longitude: '', location_label: '', service_radius_km: '5' })
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  useEffect(() => { api<typeof form>('/vendors/location/').then(data=>setForm({...data,service_radius_km:String(data.service_radius_km)})).catch(()=>undefined) }, [])
  const locate = () => navigator.geolocation?.getCurrentPosition(({coords})=>setForm(current=>({...current,latitude:String(coords.latitude),longitude:String(coords.longitude)})),()=>setError('Location access denied. Enter coordinates manually.'))
  const save = async (event: FormEvent) => {
    event.preventDefault(); setLoading(true); setError(''); setNotice('')
    try { await api('/vendors/location/',{method:'PUT',body:JSON.stringify({...form,service_radius_km:Number(form.service_radius_km)})}); setNotice('Your location and service area were saved.') }
    catch(err) { setError(err instanceof Error ? err.message : 'Could not save location.') }
    finally { setLoading(false) }
  }
  const field='mt-1 w-full rounded-xl border border-slate-200 px-3 py-3'
  return <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6"><div className="page-hero p-6 sm:p-8"><p className="eyebrow">Seller settings</p><h1 className="mt-2 text-3xl font-black">Set your service area</h1><p className="mt-3 text-sm text-slate-600">Add your shop or operating-area coordinates so nearby buyers can discover your listings and you can see relevant buyer requests.</p></div>
    <form onSubmit={save} className="mt-6 space-y-4 rounded-3xl border bg-white p-6">
      {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{notice && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p>}
      <button type="button" onClick={locate} className="rounded-xl border px-4 py-3 text-sm font-bold"><LocateFixed className="mr-2 inline h-4 w-4" />Use this device location</button>
      <div className="grid grid-cols-2 gap-3"><label className="text-sm font-semibold">Latitude<input required type="number" step="any" min="-90" max="90" value={form.latitude} onChange={e=>setForm({...form,latitude:e.target.value})} className={field} /></label><label className="text-sm font-semibold">Longitude<input required type="number" step="any" min="-180" max="180" value={form.longitude} onChange={e=>setForm({...form,longitude:e.target.value})} className={field} /></label></div>
      <label className="block text-sm font-semibold">Public location label<input value={form.location_label} onChange={e=>setForm({...form,location_label:e.target.value})} className={field} placeholder="e.g. Near MAU main gate" /></label>
      <label className="block text-sm font-semibold">Service area<select value={form.service_radius_km} onChange={e=>setForm({...form,service_radius_km:e.target.value})} className={field}><option value="1">1 km</option><option value="3">3 km</option><option value="5">5 km</option><option value="10">10 km</option><option value="20">20 km</option><option value="50">50 km</option></select></label>
      <p className="flex gap-2 text-xs text-slate-500"><ShieldCheck className="h-4 w-4 shrink-0" />Your exact coordinates are used for distance matching and are not included in public vendor profiles. Only your location label is public.</p>
      <button disabled={loading} className="w-full rounded-xl bg-slate-950 px-5 py-3 font-bold text-white">{loading?'Saving…':'Save service area'}</button>
    </form>
  </main>
}
