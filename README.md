# Experiment 1 — First-Price Auction (oTree)

Single-app oTree project for a 2-player first-price sealed-bid auction (random matching, 10 rounds).

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U otree
export OTREE_ADMIN_PASSWORD=otree
otree devserver
```
Open the URL → admin (`admin/otree`) → **Create session → exp1_first_price_random**.

## Deploy (GitHub → Heroku via oTree Hub)
1. Push this folder to a GitHub repo.
2. On oTree Hub → Heroku → New app (or your app) → Deploy from GitHub → select the repo → Deploy.
3. In Heroku **Settings → Config Vars**, set `OTREE_ADMIN_PASSWORD`.
4. Provision **Heroku Postgres (Essential-0)** in **Resources**.
5. Open `/admin` → Create session → `exp1_first_price_random`.
