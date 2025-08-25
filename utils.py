from typing import Tuple

def safe_float(s, default=0.0) -> float:
    try:
        if s is None:
            return float(default)
        return float(str(s).replace(",", ".").strip())
    except Exception:
        return float(default)

def kg_to_bag_repr(total_kg: float, poids_sac_kg: float) -> str:
    poids = float(poids_sac_kg or 0)
    if poids <= 0:
        return f"{total_kg:.2f} kg"
    sacs = int(total_kg // poids)
    reste = total_kg - sacs * poids
    if sacs > 0 and reste > 0:
        return f"{sacs} sac(s) + {reste:.2f} kg"
    if sacs > 0:
        return f"{sacs} sac(s)"
    return f"{reste:.2f} kg"

def bags_to_kg(nb_sacs: float, poids_sac_kg: float) -> float:
    return float(nb_sacs) * float(poids_sac_kg)

def kg_to_bags(qty_kg: float, poids_sac_kg: float) -> Tuple[int, float]:
    poids = float(poids_sac_kg or 0)
    if poids <= 0:
        return (0, qty_kg)
    sacs = int(qty_kg // poids)
    reste = qty_kg - sacs * poids
    return sacs, reste