# SurePlug discovery features

This branch adds two connected marketplace features: location-aware discovery and buyer demand signals.

## Nearby discovery

- Buyers can use browser geolocation or enter coordinates manually, then search within 1, 3, 5, 10, 20 or 50 km.
- The API returns active vendors and published, available listings with approximate distance.
- Sellers save a shop/operating coordinate, a public location label, and a service radius from their dashboard.
- Public vendor responses expose the seller's location label, not the saved coordinates.
- Browser coordinates used by the nearby search are query parameters for that request and are not stored by the API.

## Buyer Signals

A signed-in buyer can post an item or service they need, optionally specifying category, description, budget range, general area, radius, urgency and an expiry duration (24 hours, 3 days or 7 days).

- Active sellers can browse matching requests and send one response per seller per request.
- A seller response can include a price, message and one of that seller's own listings.
- Buyers can see their requests and seller responses, pause an active request, mark it fulfilled, close it, or delete it.
- Expired requests are automatically marked expired when the buyer/seller request feed is read.
- Exact buyer coordinates are write-only API fields. Sellers see the buyer's general area label and radius, not precise coordinates.

## API endpoints

All endpoints are under `/api/v1/`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `nearby/?latitude=...&longitude=...&radius_km=5&kind=all` | Public | Find nearby sellers and listings |
| GET | `seller/location/` | Signed-in seller | Read own saved location |
| PUT | `vendors/location/` | Signed-in seller | Save or update coordinates, label and service radius |
| GET | `buyer-signals/` | Signed-in user | Sellers see active matching requests; buyers see their own requests and responses |
| POST | `buyer-signals/` | Signed-in user | Publish a buyer request |
| PATCH | `buyer-signals/{id}/` | Request owner | Edit or change status |
| DELETE | `buyer-signals/{id}/` | Request owner | Delete a request |
| POST | `buyer-signals/{id}/respond/` | Active seller | Respond with message, optional price and optional own listing |

The nearby endpoint accepts `kind=all`, `kind=products` or `kind=vendors`. Coordinates must be valid latitude/longitude values and the radius must be between 1 and 100 km.

## Local validation

From `backend/`:

```powershell
python manage.py migrate
python manage.py check
python manage.py test accounts products moderation discovery
python manage.py makemigrations --check --dry-run
```

From `frontend/`:

```powershell
npm ci
npm run build
```

A GitHub Actions workflow on this branch runs these backend checks and the frontend production build for pushes and pull requests.

## Current implementation boundary

Distance calculations currently use the Haversine formula over seller location records. This is appropriate for the current MVP scale. For a large marketplace, move distance filtering into PostgreSQL/PostGIS or a database bounding-box query with spatial indexes. Do not expose raw buyer or seller coordinates in public serializers. Browser geolocation requires HTTPS and user permission.