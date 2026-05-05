# DREAD Risk Scoring System

Designed by Waleed Ahmad.

The system calculates a DREAD score by averaging five 1‑5 ratings:
- Damage
- Reproducibility
- Exploitability
- Affected Users
- Discoverability

The auto‑calculation is performed in Threat.calculate_dread() (models.py).
Risk levels are then assigned automatically:
- DREAD < 2 → Low
- 2‑3 → Medium
- 3‑4 → High
- ≥ 4 → Critical
