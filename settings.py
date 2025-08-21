# settings.py  (repo root)
from os import environ

SESSION_CONFIGS = [
    dict(
        name='experiment1',
        display_name='Experiment 1: First-Price (random matching)',
        app_sequence=['experiment1'],
        num_demo_participants=2,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc='',
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# Set this in Heroku → Settings → Config Vars (OTREE_ADMIN_PASSWORD)
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'otree')  # change/remove default in prod

# Set this in Heroku as OTREE_SECRET_KEY; fallback is fine for local dev
SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'dev-key-change-me')

# REQUIRED by oTree
INSTALLED_APPS = ['otree']

