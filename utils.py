from typing import Tuple

def safe_float(value, default=0.0):
    """Convertit une chaîne en flottant, gère les erreurs de conversion."""
    try:
        return float(value.replace(',', '.'))
    except (ValueError, TypeError):
        return default


# --- Module utils.py (inchangé) ---
def kg_to_bag_repr(qty_kg: float, bag_weight_kg: float) -> str:
    """
    Convertit un poids en kg en une représentation en sacs et kg restants.
    Ex: 54 kg avec des sacs de 50 kg -> "1 sac et 4 kg"
    """
    if bag_weight_kg <= 0:
        return f"{qty_kg:,.2f} kg"
    
    num_bags = int(qty_kg // bag_weight_kg)
    remaining_kg = qty_kg % bag_weight_kg
    
    parts = []
    if num_bags > 0:
        parts.append(f"{num_bags} sac{'s' if num_bags > 1 else ''}")
    if remaining_kg > 0:
        parts.append(f"{remaining_kg:,.2f} kg")
    
    return " et ".join(parts) if parts else "0 kg"






def bags_to_kg(nb_sacs: float, poids_sac_kg: float) -> float:
    return float(nb_sacs) * float(poids_sac_kg)

def kg_to_bags(qty_kg: float, poids_sac_kg: float) -> Tuple[int, float]:
    poids = float(poids_sac_kg or 0)
    if poids <= 0:
        return (0, qty_kg)
    sacs = int(qty_kg // poids)
    reste = qty_kg - sacs * poids
    return sacs, reste