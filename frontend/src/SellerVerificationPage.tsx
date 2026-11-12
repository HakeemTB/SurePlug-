import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

const API_BASE = 'https://sureplug-0q7j.onrender.com/api/v1'

type Submission = {
  id: number
  legal_name: string
  document_type: string
  document_last4: string
  contact_phone: string
  status: 'pending' | 'approved' | 'rejected'
  admin_notes: string
  submitted_at: string
  reviewed_at: string | null
}

type VerificationData = {
  is_verified: boolean
  submission: Submission | null
}

function csrfToken() {
  const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))
  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : ''
}

async function request<T>(method = 'GET', body?: unknown): Promise<T> {
  const headers = new Headers({ Accept: 'application/json' })
  if (body !== undefined) headers.set('Content-Type', 'application/json')
  if (method !== 'GET') {
    const token = csrfToken()
    if (token) headers.set('X-CSRFToken', token)
  }
  const response = await fetch(`${API_BASE}/vendors/verification/`, {
    method, headers, credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const values = Object.values(payload as Record<string, unknown>)
    const message = values.flatMap(value => Array.isArray(value) ? value : [value]).find(value => typeof value === 'string')
    throw new Error(typeof message === 'string' ? message : `Request failed (${response.status})`)
  }
  return payload as T
}

const documentOptions = [
  ['nin', 'National Identification Number (NIN)'],
  ['voters_card', "Voter's card"],
  ['drivers_license', "Driver's licence"],
  ['passport', 'International passport'],
  ['student_id', 'Institutional/student ID'],
  ['business_document', 'Business registration document'],
]

export function SellerVerificationPage() {
  const [data, setData] = useState<VerificationData | null>(null)
  const [form, setForm] = useState({ legal_name: '', document_type: 'student_id', document_last4: '', contact_phone: '' })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const refresh = () => request<VerificationData>().then(setData).catch(err => setError(err instanceof Error ? err.message : 'Sign in with a seller account to continue.')).finally(() => setLoading(false))
  useEffect(() => { void refresh() }, [])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true); setError(''); setNotice('')
    try {
      const result = await request<{ message: string; submission: Submission }>('POST', form)
      setData(current => current ? { ...current, submission: result.submission } : current)
      setNotice(result.message)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit verification details.')
    } finally {
      setSubmitting(false)
    }
  }

  const submission = data?.submission
  const canSubmit = !data?.is_verified && submission?.status !== 'pending'
  const field = 'mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-3'

  if (loading) return <main className="mx-auto max-w-3xl px-4 py-12">Loading seller verification…</main>

  return <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <p className="text-xs font-bold uppercase tracking-widest text-orange-600">Trust and safety</p>
      <h1 className="mt-2 text-3xl font-black text-slate-950">Seller identity verification</h1>
      <p className="mt-3 text-sm leading-6 text-slate-600">SurePlug allows sellers to register, but seller verification is required before new listings can be approved and published. Our team reviews submissions manually.</p>
      {error && <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      {notice && <p role="status" className="mt-5 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p>}

      {data?.is_verified ? <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5"><p className="font-bold text-emerald-800">Your seller account is verified.</p><p className="mt-1 text-sm text-emerald-700">You can submit listings for moderation and approval.</p></div> : submission?.status === 'pending' ? <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5"><p className="font-bold text-amber-800">Verification is awaiting review.</p><p className="mt-1 text-sm text-amber-700">Submitted {new Date(submission.submitted_at).toLocaleString()}. You can continue managing drafts while our team reviews your details.</p></div> : null}

      {submission?.status === 'rejected' && <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-5"><p className="font-bold text-rose-800">Further review is required.</p><p className="mt-1 text-sm text-rose-700">{submission.admin_notes || 'Please check your details and submit again, or contact SurePlug support.'}</p></div>}

      {canSubmit && <form onSubmit={submit} className="mt-7 space-y-4">
        <h2 className="text-lg font-bold">Submit verification details</h2>
        <label className="block text-sm font-semibold">Full legal name<input required maxLength={180} value={form.legal_name} onChange={e=>setForm({...form,legal_name:e.target.value})} className={field} autoComplete="name" /></label>
        <label className="block text-sm font-semibold">Document type<select value={form.document_type} onChange={e=>setForm({...form,document_type:e.target.value})} className={field}>{documentOptions.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
        <label className="block text-sm font-semibold">Last four characters of document reference<input required minLength={4} maxLength={4} pattern="[A-Za-z0-9]{4}" value={form.document_last4} onChange={e=>setForm({...form,document_last4:e.target.value.toUpperCase()})} className={field} autoComplete="off" /></label>
        <label className="block text-sm font-semibold">Contact phone number<input required maxLength={30} value={form.contact_phone} onChange={e=>setForm({...form,contact_phone:e.target.value})} className={field} autoComplete="tel" /></label>
        <div className="rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-600">Privacy: enter only the final four characters requested above. Do not enter your full NIN, passport number or other complete identity number here. This initial workflow does not collect ID images; any additional document check must be handled through a secure channel.</div>
        <button disabled={submitting} className="w-full rounded-xl bg-slate-950 px-5 py-3 font-bold text-white disabled:opacity-60">{submitting ? 'Submitting…' : 'Submit for verification'}</button>
      </form>}

      <div className="mt-7 flex flex-wrap gap-3 border-t border-slate-100 pt-5 text-sm">
        <Link to="/dashboard" className="font-semibold text-slate-700 underline">Back to seller dashboard</Link>
        <Link to="/products" className="font-semibold text-slate-700 underline">Browse marketplace</Link>
      </div>
    </div>
  </main>
}
