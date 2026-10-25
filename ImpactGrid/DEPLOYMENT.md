# Deploy ImpactGrid

## Recommended: Render
1. Create a GitHub account if you don't already have one.
2. Create a new repository and upload the contents of this project ZIP (not the ZIP file itself).
3. In Render, choose **New + → Blueprint**, connect the repository, and select `render.yaml`.
4. Review the service and deploy. Render may require a paid plan for persistent disk; if disk is not available on your plan, do not use SQLite for important long-term data. Use a managed PostgreSQL service and update the app before production.
5. After deployment, open the generated `https://...onrender.com` URL.
6. Check `/api/health` and `/docs`.

## AI key
The app runs without an AI key using a local fallback. For live AI responses, set `OPENAI_API_KEY` in the hosting provider's environment variables. Keep the key private and never paste it into frontend code or public GitHub. API usage may incur charges.

## Important
- This is a hackathon prototype, not a production-ready service for real health, donor, payment, or emergency use.
- Donor finder entries are not verified. Do not rely on this demo to locate emergency blood.
- Crop checker is educational triage, not a diagnosis.
- Protect personal data, add rate limits, privacy terms, monitoring and proper verification before public use.
