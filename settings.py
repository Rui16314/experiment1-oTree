import os
from os import environ

SESSION_CONFIGS = [
    dict(
        name='exp1_first_price_random',
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
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'otree')

DEMO_PAGE_INTRO_HTML = '<p>Experiment 1: First-price sealed-bid auction with random matching.</p>'

SECRET_KEY = 'dev-key-change-me'
