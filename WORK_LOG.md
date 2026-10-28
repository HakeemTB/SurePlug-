# SurePlug Work Log

## 2026-10-13

### Scope

Complete the outstanding MVP follow-up: provide repeatable local demo data, make account and listing API flows reliable, exercise the important flows with automated tests, and connect the vendor dashboard to real session authentication. This log records implementation progress and validation results.

### Progress

- [x] Confirmed the backend, frontend, and current MVP endpoints are present.
- [x] Harden account registration, product CRUD, discovery filters, and report submission.
- [x] Add an idempotent demo-data command and local testing instructions.
- [x] Add API tests for account, discovery, ownership, and reports.
- [x] Connect vendor dashboard sign-in/registration and verify frontend build.

### Implementation notes

- Account registration now validates passwords, creates the user and vendor profile atomically, and signs the new vendor into a session.
- Product discovery validates filter inputs, applies campus/category/price/search filters, and never exposes drafts or inactive sellers through public detail endpoints.
- Product create/update validates non-negative prices; update and delete enforce ownership and return 404 for missing products. Duplicate product names get stable unique slugs.
- Reports must reference a product or vendor, and public report submissions cannot set moderation status.
- Added `seed_demo_data` for two campuses, four categories, three demo vendors, and six sample products; rerunning updates these records without resetting existing demo passwords.
- The dashboard now supports sign-in, vendor registration, listing creation, publish/unpublish, deletion, and visible request errors.

### Validation

- Initial API test run exposed two issues (negative prices were accepted on edit and the test campus filter used a zone rather than the campus name); both were corrected.
- Django system checks and migration consistency passed.
- Backend API tests passed (11 tests before the final negative-create regression test was added).
- Demo data was seeded successfully.
- Frontend TypeScript and production build passed.
- Final backend run passed: 12 tests; Django system checks reported no issues; no model migration changes are pending.
- Ran the seed command twice and verified the same 2 campuses, 4 categories, 3 demo vendors, and 6 sample products remained.
- Frontend TypeScript compilation and Vite production build passed.
- Verified the live Vite proxy: health and public products returned successfully; demo sign-in and protected dashboard worked; a temporary product was created and deleted with the session/CSRF cookie flow; no temporary listing remained.
- Opened the browser dashboard and confirmed the signed-in vendor sees their stats, listings, and listing form.

### Completion

The tracked MVP follow-up tasks are complete. The development servers remain available at `http://127.0.0.1:5173/` (frontend) and `http://127.0.0.1:8000/` (backend). The demo accounts and default password are strictly for local testing; see the root README for run and seed instructions.

## Phase 2 — Frontend UI/UX pass (2026-10-28)

- Added shared responsive site navigation and footer so every route has consistent wayfinding.
- Redesigned the homepage with a more prominent marketplace search, campus-focused messaging, category navigation, featured product-card styling, skeleton loading states, and a seller call-to-action.
- Connected homepage search submission to `/products?search=...` and initialized the listings search from the URL query parameter.
- Improved product cards with campus/vendor context, stock availability labels, featured tags, and stronger hover/focus affordances.
- Improved the listings page with a refreshed heading, results count, filter reset actions, and skeleton/empty states.
- Improved vendor directory loading, error, and empty states; added verified-seller presentation.
- Improved product detail and vendor storefront loading/error/empty states.
- Added responsive styles, focus-visible styling, and reduced-motion handling.
- Backend routes and API request contracts were not intentionally changed.
- Validation limitation: this environment could not complete `npm ci` before timeout, leaving the dependency folders incomplete; therefore a fresh full frontend build could not be verified here. The TSX parser reported no syntax errors, but module/type errors remain until dependencies are installed. Run `npm ci` and `npm run build` in the project's frontend directory on the development machine before treating this UI pass as verified.
