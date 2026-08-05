"""
PulseConnect v2 — backend configuration.

SEASONS: the 6 seasons the pipeline pulls from FastF1 (2021-2026).
TEAMS: 2026 grid. `founded_season` marks brand-new constructors (Cadillac, Audi)
       so the pipeline knows to emit "unknown" for any season before they existed.
DRIVERS: `debut_season` marks when a driver's F1 career began, same purpose —
       a rookie has no history to compute consistency/pace stats from.

Real historical values only exist once you run `pipeline/build_dataset.py`
with FastF1 able to reach the network (this scaffold ships with a seed
dataset of the same shape so the frontend has something to render).
"""

SEASONS = [2021, 2022, 2023, 2024, 2025, 2026]
CURRENT_SEASON = 2026
CACHE_DIR = "data/cache"
GENERATED_DIR = "data/generated"
SEED_DIR = "data/seed"

UNKNOWN = "unknown"  # sentinel used throughout instead of fabricating a number

TEAMS = [
    {"id": "redbull", "name": "Oracle Red Bull Racing", "short": "RBR", "accent": "#2C5CC5",
     "founded_season": None, "engine": "Red Bull Ford", "drivers": ["VER", "HAD"]},
    {"id": "ferrari", "name": "Scuderia Ferrari HP", "short": "FER", "accent": "#E8002D",
     "founded_season": None, "engine": "Ferrari", "drivers": ["LEC", "HAM"]},
    {"id": "mercedes", "name": "Mercedes-AMG PETRONAS Formula One Team", "short": "MER", "accent": "#27BFA3",
     "founded_season": None, "engine": "Mercedes", "drivers": ["RUS", "ANT"]},
    {"id": "mclaren", "name": "McLaren Mastercard F1 Team", "short": "MCL", "accent": "#FF8700",
     "founded_season": None, "engine": "Mercedes", "drivers": ["NOR", "PIA"]},
    {"id": "astonmartin", "name": "Aston Martin Aramco Formula One Team", "short": "AMR", "accent": "#1E8262",
     "founded_season": None, "engine": "Honda", "drivers": ["ALO", "STR"]},
    {"id": "alpine", "name": "BWT Alpine Formula One Team", "short": "ALP", "accent": "#2E86D6",
     "founded_season": None, "engine": "Renault", "drivers": ["GAS", "COL"]},
    {"id": "racingbulls", "name": "Visa Cash App Racing Bulls F1 Team", "short": "VCARB", "accent": "#5B7CFF",
     "founded_season": None, "engine": "Red Bull Ford", "drivers": ["LAW", "LIN"]},
    {"id": "haas", "name": "TGR Haas F1 Team", "short": "HAA", "accent": "#B6BABD",
     "founded_season": None, "engine": "Ferrari", "drivers": ["OCO", "BEA"]},
    {"id": "audi", "name": "Audi Revolut F1 Team", "short": "AUDI", "accent": "#BB0A30",
     "founded_season": 2026, "engine": "Audi", "drivers": ["HUL", "BOR"]},
    {"id": "williams", "name": "Atlassian Williams F1 Team", "short": "WIL", "accent": "#5AC5F2",
     "founded_season": None, "engine": "Mercedes", "drivers": ["ALB", "SAI"]},
    {"id": "cadillac", "name": "Cadillac Formula 1 Team", "short": "CAD", "accent": "#8A8D8F",
     "founded_season": 2026, "engine": "Ferrari", "drivers": ["PER", "BOT"]},
]

DRIVERS = [
    {"id": "VER", "name": "Max Verstappen", "num": 3, "country": "NL", "debut_season": 2015},
    {"id": "HAD", "name": "Isack Hadjar", "num": 6, "country": "FR", "debut_season": 2025},
    {"id": "LEC", "name": "Charles Leclerc", "num": 16, "country": "MC", "debut_season": 2018},
    {"id": "HAM", "name": "Lewis Hamilton", "num": 44, "country": "GB", "debut_season": 2007},
    {"id": "RUS", "name": "George Russell", "num": 63, "country": "GB", "debut_season": 2019},
    {"id": "ANT", "name": "Kimi Antonelli", "num": 12, "country": "IT", "debut_season": 2025},
    {"id": "NOR", "name": "Lando Norris", "num": 1, "country": "GB", "debut_season": 2019},
    {"id": "PIA", "name": "Oscar Piastri", "num": 81, "country": "AU", "debut_season": 2023},
    {"id": "ALO", "name": "Fernando Alonso", "num": 14, "country": "ES", "debut_season": 2001},
    {"id": "STR", "name": "Lance Stroll", "num": 18, "country": "CA", "debut_season": 2017},
    {"id": "GAS", "name": "Pierre Gasly", "num": 10, "country": "FR", "debut_season": 2017},
    {"id": "COL", "name": "Franco Colapinto", "num": 43, "country": "AR", "debut_season": 2024},
    {"id": "LAW", "name": "Liam Lawson", "num": 30, "country": "NZ", "debut_season": 2023},
    {"id": "LIN", "name": "Arvid Lindblad", "num": 41, "country": "GB", "debut_season": 2026},
    {"id": "OCO", "name": "Esteban Ocon", "num": 31, "country": "FR", "debut_season": 2016},
    {"id": "BEA", "name": "Oliver Bearman", "num": 87, "country": "GB", "debut_season": 2024},
    {"id": "HUL", "name": "Nico Hulkenberg", "num": 27, "country": "DE", "debut_season": 2010},
    {"id": "BOR", "name": "Gabriel Bortoleto", "num": 5, "country": "BR", "debut_season": 2025},
    {"id": "ALB", "name": "Alex Albon", "num": 23, "country": "TH", "debut_season": 2019},
    {"id": "SAI", "name": "Carlos Sainz", "num": 55, "country": "ES", "debut_season": 2015},
    {"id": "PER", "name": "Sergio Perez", "num": 11, "country": "MX", "debut_season": 2011},
    {"id": "BOT", "name": "Valtteri Bottas", "num": 77, "country": "FI", "debut_season": 2013},
]

CIRCUITS = [
    {"id": "bahrain", "name": "Bahrain International Circuit", "country": "Bahrain", "type": "Balanced", "length_km": 5.41, "corners": 15},
    {"id": "jeddah", "name": "Jeddah Corniche Circuit", "country": "Saudi Arabia", "type": "Street", "length_km": 6.17, "corners": 27},
    {"id": "melbourne", "name": "Albert Park Circuit", "country": "Australia", "type": "Balanced", "length_km": 5.28, "corners": 14},
    {"id": "baku", "name": "Baku City Circuit", "country": "Azerbaijan", "type": "Street", "length_km": 6.00, "corners": 20},
    {"id": "miami", "name": "Miami International Autodrome", "country": "USA", "type": "Balanced", "length_km": 5.41, "corners": 19},
    {"id": "monaco", "name": "Circuit de Monaco", "country": "Monaco", "type": "Street", "length_km": 3.34, "corners": 19},
    {"id": "catalunya", "name": "Circuit de Barcelona-Catalunya", "country": "Spain", "type": "Technical", "length_km": 4.66, "corners": 14},
    {"id": "montreal", "name": "Circuit Gilles Villeneuve", "country": "Canada", "type": "Mixed", "length_km": 4.36, "corners": 14},
    {"id": "spielberg", "name": "Red Bull Ring", "country": "Austria", "type": "Power", "length_km": 4.32, "corners": 10},
    {"id": "silverstone", "name": "Silverstone Circuit", "country": "United Kingdom", "type": "Balanced", "length_km": 5.89, "corners": 18},
    {"id": "hungaroring", "name": "Hungaroring", "country": "Hungary", "type": "Technical", "length_km": 4.38, "corners": 14},
    {"id": "spa-francorchamps", "name": "Circuit de Spa-Francorchamps", "country": "Belgium", "type": "High-Speed", "length_km": 7.00, "corners": 19},
    {"id": "zandvoort", "name": "Circuit Zandvoort", "country": "Netherlands", "type": "Technical", "length_km": 4.26, "corners": 14},
    {"id": "monza", "name": "Autodromo Nazionale Monza", "country": "Italy", "type": "Power", "length_km": 5.79, "corners": 11},
    {"id": "madring", "name": "Madrid In-Motion Ring", "country": "Spain", "type": "Balanced", "length_km": 5.47, "corners": 20},
    {"id": "baku", "name": "Baku City Circuit", "country": "Azerbaijan", "type": "Street", "length_km": 6.00, "corners": 20},
    {"id": "marina-bay", "name": "Marina Bay Street Circuit", "country": "Singapore", "type": "Street", "length_km": 4.94, "corners": 19},
    {"id": "suzuka", "name": "Suzuka International Racing Course", "country": "Japan", "type": "Technical", "length_km": 5.81, "corners": 18},
    {"id": "lusail", "name": "Lusail International Circuit", "country": "Qatar", "type": "High-Speed", "length_km": 5.38, "corners": 16},
    {"id": "austin", "name": "Circuit of the Americas", "country": "USA", "type": "Mixed", "length_km": 5.51, "corners": 20},
    {"id": "mexico-city", "name": "Autodromo Hermanos Rodriguez", "country": "Mexico", "type": "Balanced", "length_km": 4.30, "corners": 17},
    {"id": "interlagos", "name": "Autodromo Jose Carlos Pace", "country": "Brazil", "type": "Mixed", "length_km": 4.31, "corners": 15},
    {"id": "las-vegas", "name": "Las Vegas Strip Circuit", "country": "USA", "type": "Power", "length_km": 6.20, "corners": 17},
    {"id": "yas-marina", "name": "Yas Marina Circuit", "country": "Abu Dhabi", "type": "Balanced", "length_km": 5.28, "corners": 16},
]

_seen = set()
CIRCUITS = [c for c in CIRCUITS if not (c["id"] in _seen or _seen.add(c["id"]))]


EVENT_NAME_TO_CIRCUIT = {
    "bahrain": "bahrain",
    "saudi arabian": "jeddah",
    "australian": "melbourne",
    "azerbaijan": "baku",
    "miami": "miami",
    "monaco": "monaco",
    "emilia romagna": "monza",  # Imola sometimes substitutes; nearest mapped circuit
    "spanish": "catalunya",
    "canadian": "montreal",
    "austrian": "spielberg",
    "british": "silverstone",
    "hungarian": "hungaroring",
    "belgian": "spa-francorchamps",
    "dutch": "zandvoort",
    "italian": "monza",
    "madrid": "madring",
    "singapore": "marina-bay",
    "japanese": "suzuka",
    "qatar": "lusail",
    "united states": "austin",
    "mexico": "mexico-city",
    "brazilian": "interlagos",
    "sao paulo": "interlagos",
    "s\u00e3o paulo": "interlagos",
    "las vegas": "las-vegas",
    "abu dhabi": "yas-marina",
}


def circuit_id_for_event(event_name):
    name = (event_name or "").lower()
    for key, circuit_id in EVENT_NAME_TO_CIRCUIT.items():
        if key in name:
            return circuit_id
    return None
