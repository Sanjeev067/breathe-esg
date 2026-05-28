def normalize_emission(scope: str, raw_value: float, raw_unit: str) -> tuple[float, str]:
    """
    Converts raw emission values into a normalized unit ('kg CO2e')
    using standard ESG/GHG Protocol emission factors.
    """
    if raw_value is None:
        return 0.0, "kg CO2e"

    val = float(raw_value)
    unit = str(raw_unit).strip().lower()
    scope = str(scope).strip().upper()

    # Define emission factors mapping
    # (Scope, Standardized Unit) -> Factor (to get kg CO2e)
    factors = {
        # Scope 1 (Direct Emissions - Stationary/Mobile Combustion)
        ("SCOPE1", "liter"): 2.3,
        ("SCOPE1", "liters"): 2.3,
        ("SCOPE1", "l"): 2.3,
        ("SCOPE1", "gallon"): 8.7,
        ("SCOPE1", "gallons"): 8.7,
        ("SCOPE1", "gal"): 8.7,
        ("SCOPE1", "kg"): 3.0,
        ("SCOPE1", "kgs"): 3.0,
        ("SCOPE1", "kilogram"): 3.0,
        ("SCOPE1", "kilograms"): 3.0,

        # Scope 2 (Indirect Emissions - Purchased Electricity/Steam/etc.)
        ("SCOPE2", "kwh"): 0.4,
        ("SCOPE2", "kilowatt-hour"): 0.4,
        ("SCOPE2", "kilowatt hour"): 0.4,
        ("SCOPE2", "mwh"): 400.0,
        ("SCOPE2", "megawatt-hour"): 400.0,
        ("SCOPE2", "megawatt hour"): 400.0,

        # Scope 3 (Other Indirect - Business Travel, Waste, Commuting)
        ("SCOPE3", "km"): 0.15,
        ("SCOPE3", "kms"): 0.15,
        ("SCOPE3", "kilometer"): 0.15,
        ("SCOPE3", "kilometers"): 0.15,
        ("SCOPE3", "mile"): 0.24,
        ("SCOPE3", "miles"): 0.24,
        ("SCOPE3", "mi"): 0.24,
        ("SCOPE3", "kg"): 0.5,
        ("SCOPE3", "kgs"): 0.5,
        ("SCOPE3", "kilogram"): 0.5,
        ("SCOPE3", "kilograms"): 0.5,
    }

    # Try lookup with (scope, unit)
    factor = factors.get((scope, unit))

    # Fallback to general unit factor if scope-specific is not found
    if factor is None:
        general_factors = {
            "kwh": 0.4,
            "kilowatt-hour": 0.4,
            "kilowatt hour": 0.4,
            "mwh": 400.0,
            "megawatt-hour": 400.0,
            "megawatt hour": 400.0,
            "liter": 2.3,
            "liters": 2.3,
            "l": 2.3,
            "gallon": 8.7,
            "gallons": 8.7,
            "gal": 8.7,
            "km": 0.15,
            "kms": 0.15,
            "kilometer": 0.15,
            "kilometers": 0.15,
            "mile": 0.24,
            "miles": 0.24,
            "mi": 0.24,
            "kg": 1.0,  # default weight fallback
            "kgs": 1.0,
            "kilogram": 1.0,
            "kilograms": 1.0,
        }
        factor = general_factors.get(unit, 1.0)  # Default to 1.0 if unit is unknown

    normalized_val = val * factor
    return round(normalized_val, 4), "kg CO2e"
