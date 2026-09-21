def get_element_compatibility(element1: str, element2: str):
    """Calculates the cosmic synergy and matchup prediction between two franchise elements."""
    element1 = element1.capitalize()
    element2 = element2.capitalize()
    
    # Same element pairing
    if element1 == element2:
        return {
            "score": 95,
            "synergy": "Elemental Resonance ??",
            "description": f"Both franchises share the {element1} sign. Expect mirrored playstyles, intense tempo, and absolute harmony on the court!"
        }
    
    # Complementary pairings (Fire + Air, Earth + Water)
    complementary = {
        ("Fire", "Air"): ("Dynamic Fuel ????", 88, "Air feeds Fire, creating an explosive, fast-break heavy offensive clinic."),
        ("Air", "Fire"): ("Dynamic Fuel ????", 88, "Air feeds Fire, creating an explosive, fast-break heavy offensive clinic."),
        ("Earth", "Water"): ("Tapestry Growth ????", 90, "Earth grounds Water, yielding an unbreakable defensive foundation and fluid ball movement."),
        ("Water", "Earth"): ("Tapestry Growth ????", 90, "Earth grounds Water, yielding an unbreakable defensive foundation and fluid ball movement.")
    }
    
    if (element1, element2) in complementary:
        title, score, desc = complementary[(element1, element2)]
        return {"score": score, "synergy": title, "description": desc}
        
    # Clashing pairings (Fire + Water, Earth + Air, etc.)
    return {
        "score": 45,
        "synergy": "Cosmic Friction ?",
        "description": f"An elemental clash between {element1} and {element2}! Expect high volatility, technical fouls, and a gritty defensive battle."
    }
