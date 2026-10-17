"""Deterministic fictional demo seed; all customer and payee records are synthetic."""
from .state import SEED, PAYEES, store

def seed_demo():
    store.reset()
    return {'customers':len(SEED),'payees':len(PAYEES),'synthetic':True}
