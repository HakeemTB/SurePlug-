# SurePlug Integration Audit — 2026-10-28

## Scope
Reviewed the uploaded project source statically, focusing on the React/Vite API client, Django URL routing, session authentication, CSRF handling, product CRUD, discovery, and media URLs.

## Confirmed issue and fix
- **Development product/vendor images could fail to load.** Django image serializers return relative `/media/...` paths when serializers are created without request context. The Vite dev server previously proxied only `/api`, so a browser requesting `/media/...` from port 5173 would not reach Django on port 8000.
- **Fix applied:** added a `/media` proxy to `frontend/vite.config.ts`.
- **Deployment documentation updated:** the production reverse proxy/static host must also route `/media/` to Django. The API and media routes should remain on the same public origin as the frontend to keep the documented session-cookie flow straightforward.

## Static review findings
- The frontend API base `/api/v1` matches the Django URL prefix and Vite `/api` proxy.
- The frontend uses `credentials: 'same-origin'`, which is appropriate for the documented same-origin session-cookie setup.
- The login and registration flow first requests `/auth/csrf/`, then sends `X-CSRFToken` on the state-changing request. Django has the CSRF cookie endpoint and CSRF-protected login/registration/logout views.
- Product create/update/delete URLs and HTTP methods in the frontend match Django URL routes.
- The frontend dashboard fetches `/vendors/dashboard/`, matching the protected backend endpoint.
- Product discovery parameters used by the API (`q`, `category`, `campus`, `min_price`, `max_price`, `availability`, `ordering`) are supported by the backend filter serializer.

## Validation limitations
- I could not execute Django checks or backend tests in this environment because Django is not installed (`ModuleNotFoundError: No module named 'django'`).
- `frontend/node_modules` is not included, so I did not run the TypeScript/Vite production build. The project includes `package-lock.json`, so run `npm ci` before `npm run build` locally.
- No live browser/session test was possible in this environment. Therefore this is a source-level audit, not a claim that all end-to-end tests have passed.

## Remaining integration checks to run on the development machine
From `backend/`:
```powershell
python manage.py check
python manage.py test accounts products moderation
python manage.py makemigrations --check --dry-run
```

From `frontend/`:
```powershell
npm ci
npm run build
```

Then run both servers and verify:
1. Open `/api/v1/health/` and the frontend.
2. Sign in with a seeded demo vendor and refresh the dashboard to confirm session persistence.
3. Create a listing, unpublish/publish it, and delete it.
4. Confirm public discovery excludes unpublished listings.
5. If any product or vendor has an uploaded image, verify the image URL loads through `/media/`.
6. Sign out, then confirm the dashboard returns to the sign-in screen.

## Frontend UI/UX pass

The follow-up UI pass adds shared responsive navigation/footer, a redesigned marketplace homepage, better product cards and category browsing, search query handoff to the listings page, clearer listing filters and reset actions, and loading/error/empty states for the listings, vendor directory, product detail, and vendor storefront routes. No backend API contract changes were intended.

A full frontend build was not completed in the patching environment because `npm ci` timed out and left dependencies incomplete. Run `npm ci` followed by `npm run build` on the development machine and fix any reported errors before deploying.
