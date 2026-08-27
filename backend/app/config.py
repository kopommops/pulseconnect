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

SEASONS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
CURRENT_SEASON = 2026
CACHE_DIR = "data/cache"
GENERATED_DIR = "data/generated"
SEED_DIR = "data/seed"

UNKNOWN = "unknown"  # sentinel used throughout instead of fabricating a number

POINTS_SYSTEM = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
SPRINT_POINTS_SYSTEM = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
MIN_RACES_FOR_PREDICTION = 10
PODIUM_PRECISION_TARGET = 0.75
TOP5_PRECISION_TARGET = 0.75
RECENT_FORM_WINDOW = 5
PIT_LOSS_HEURISTIC_BY_TYPE = {
    "Street": 24.0, "Technical": 22.0, "Balanced": 21.0,
    "Mixed": 20.5, "Power": 19.0, "High-Speed": 19.5,
}
EVENT_ROSTER_OVERRIDES = {
    # 2026 Dutch GP: Hadjar injured, Lawson (normally Racing Bulls) covers
    # at Red Bull; Tsunoda + Lindblad race for Racing Bulls.
    "2026-zandvoort": {
        "redbull": ["VER", "LAW"],
        "racingbulls": ["TSU", "LIN"],
    },
}

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
    {"id": "VER", "name": "Max Verstappen", "num": 3, "country": "NL", "debut_season": 2015, "birth_date": "1997-09-30"},
    {"id": "HAD", "name": "Isack Hadjar", "num": 6, "country": "FR", "debut_season": 2025, "birth_date": "2004-09-28"},
    {"id": "LEC", "name": "Charles Leclerc", "num": 16, "country": "MC", "debut_season": 2018, "birth_date": "1997-10-16"},
    {"id": "HAM", "name": "Lewis Hamilton", "num": 44, "country": "GB", "debut_season": 2007, "birth_date": "1985-01-07"},
    {"id": "RUS", "name": "George Russell", "num": 63, "country": "GB", "debut_season": 2019, "birth_date": "1998-02-15"},
    {"id": "ANT", "name": "Kimi Antonelli", "num": 12, "country": "IT", "debut_season": 2025, "birth_date": "2006-08-25"},
    {"id": "NOR", "name": "Lando Norris", "num": 1, "country": "GB", "debut_season": 2019, "birth_date": "1999-11-13"},
    {"id": "PIA", "name": "Oscar Piastri", "num": 81, "country": "AU", "debut_season": 2023, "birth_date": "2001-04-06"},
    {"id": "ALO", "name": "Fernando Alonso", "num": 14, "country": "ES", "debut_season": 2001, "birth_date": "1981-07-29"},
    {"id": "STR", "name": "Lance Stroll", "num": 18, "country": "CA", "debut_season": 2017, "birth_date": "1998-10-29"},
    {"id": "GAS", "name": "Pierre Gasly", "num": 10, "country": "FR", "debut_season": 2017, "birth_date": "1996-02-07"},
    {"id": "COL", "name": "Franco Colapinto", "num": 43, "country": "AR", "debut_season": 2024, "birth_date": "2003-05-27"},
    {"id": "LAW", "name": "Liam Lawson", "num": 30, "country": "NZ", "debut_season": 2023, "birth_date": "2002-02-11"},
    {"id": "LIN", "name": "Arvid Lindblad", "num": 41, "country": "GB", "debut_season": 2026, "birth_date": "2007-08-08"},
    {"id": "OCO", "name": "Esteban Ocon", "num": 31, "country": "FR", "debut_season": 2016, "birth_date": "1996-09-17"},
    {"id": "BEA", "name": "Oliver Bearman", "num": 87, "country": "GB", "debut_season": 2024, "birth_date": "2005-05-08"},
    {"id": "HUL", "name": "Nico Hulkenberg", "num": 27, "country": "DE", "debut_season": 2010, "birth_date": "1987-08-19"},
    {"id": "BOR", "name": "Gabriel Bortoleto", "num": 5, "country": "BR", "debut_season": 2025, "birth_date": "2004-10-14"},
    {"id": "ALB", "name": "Alex Albon", "num": 23, "country": "TH", "debut_season": 2019, "birth_date": "1996-03-23"},
    {"id": "SAI", "name": "Carlos Sainz", "num": 55, "country": "ES", "debut_season": 2015, "birth_date": "1994-09-01"},
    {"id": "PER", "name": "Sergio Perez", "num": 11, "country": "MX", "debut_season": 2011, "birth_date": "1990-01-26"},
    {"id": "BOT", "name": "Valtteri Bottas", "num": 77, "country": "FI", "debut_season": 2013, "birth_date": "1989-08-28"},

    {"id": "TSU", "name": "Yuki Tsunoda", "num": 22, "country": "JP", "debut_season": 2021, "birth_date": "2000-05-11"},
    {"id": "IWA", "name": "Ayumu Iwasa", "num": None, "country": "JP", "debut_season": None, "birth_date": "2001-09-22"},
    {"id": "VES", "name": "Frederik Vesti", "num": None, "country": "DK", "debut_season": None, "birth_date": "2002-01-13"},
    {"id": "GIO", "name": "Antonio Giovinazzi", "num": None, "country": "IT", "debut_season": 2019, "birth_date": "1993-12-14"},
    {"id": "OWA", "name": "Pato O'Ward", "num": None, "country": "MX", "debut_season": None, "birth_date": "1999-05-06"},
    {"id": "FOR", "name": "Leonardo Fornaroli", "num": None, "country": "IT", "debut_season": None, "birth_date": "2004-12-03"},
    {"id": "CRA", "name": "Jak Crawford", "num": None, "country": "US", "debut_season": None, "birth_date": "2005-05-02"},
    {"id": "ARO", "name": "Paul Aron", "num": None, "country": "EE", "debut_season": None, "birth_date": "2004-02-04"},
    {"id": "MAI", "name": "Kush Maini", "num": None, "country": "IN", "debut_season": None, "birth_date": "2000-09-22"},
    {"id": "BRO", "name": "Luke Browning", "num": None, "country": "GB", "debut_season": None, "birth_date": "2002-01-31"},
    {"id": "DOO", "name": "Jack Doohan", "num": None, "country": "AU", "debut_season": 2024, "birth_date": "2003-01-20"},
    {"id": "HIR", "name": "Ryo Hirakawa", "num": None, "country": "JP", "debut_season": None, "birth_date": "1994-03-07"},
    {"id": "ZHO", "name": "Guanyu Zhou", "num": None, "country": "CN", "debut_season": 2022, "birth_date": "1999-05-30"},
]

RESERVE_DRIVERS = {
    "redbull": ["TSU", "IWA"],
    "racingbulls": ["TSU", "IWA"],
    "mercedes": ["VES"],
    "ferrari": ["GIO"],
    "mclaren": ["OWA", "FOR"],
    "astonmartin": ["CRA"],
    "alpine": ["ARO", "MAI"],
    "williams": ["BRO"],
    "haas": ["DOO", "HIR"],
    "cadillac": ["ZHO"],
    # Audi: no reserve announced as of this config's last edit.
}

CIRCUITS = [
    {"id": "shanghai", "name": "Shanghai International Circuit", "country": "China", "type": "Balanced", "length_km": 5.45, "corners": 16, "lat": 31.3389, "lon": 121.22},
    {"id": "bahrain", "name": "Bahrain International Circuit", "country": "Bahrain", "type": "Balanced", "length_km": 5.41, "corners": 15, "lat": 26.0325, "lon": 50.5106},
    {"id": "jeddah", "name": "Jeddah Corniche Circuit", "country": "Saudi Arabia", "type": "Street", "length_km": 6.17, "corners": 27, "lat": 21.6319, "lon": 39.1044},
    {"id": "melbourne", "name": "Albert Park Circuit", "country": "Australia", "type": "Balanced", "length_km": 5.28, "corners": 14, "lat": -37.8497, "lon": 144.968},
    {"id": "baku", "name": "Baku City Circuit", "country": "Azerbaijan", "type": "Street", "length_km": 6.00, "corners": 20, "lat": 40.3725, "lon": 49.8533},
    {"id": "miami", "name": "Miami International Autodrome", "country": "USA", "type": "Balanced", "length_km": 5.41, "corners": 19, "lat": 25.9581, "lon": -80.2389},
    {"id": "monaco", "name": "Circuit de Monaco", "country": "Monaco", "type": "Street", "length_km": 3.34, "corners": 19, "lat": 43.7347, "lon": 7.4206},
    {"id": "catalunya", "name": "Circuit de Barcelona-Catalunya", "country": "Spain", "type": "Technical", "length_km": 4.66, "corners": 14, "lat": 41.57, "lon": 2.2611},
    {"id": "montreal", "name": "Circuit Gilles Villeneuve", "country": "Canada", "type": "Mixed", "length_km": 4.36, "corners": 14, "lat": 45.5, "lon": -73.5228},
    {"id": "spielberg", "name": "Red Bull Ring", "country": "Austria", "type": "Power", "length_km": 4.32, "corners": 10, "lat": 47.2197, "lon": 14.7647},
    {"id": "silverstone", "name": "Silverstone Circuit", "country": "United Kingdom", "type": "Balanced", "length_km": 5.89, "corners": 18, "lat": 52.0786, "lon": -1.0169},
    {"id": "hungaroring", "name": "Hungaroring", "country": "Hungary", "type": "Technical", "length_km": 4.38, "corners": 14, "lat": 47.5789, "lon": 19.2486},
    {"id": "spa-francorchamps", "name": "Circuit de Spa-Francorchamps", "country": "Belgium", "type": "High-Speed", "length_km": 7.00, "corners": 19, "lat": 50.4372, "lon": 5.9714},
    {"id": "zandvoort", "name": "Circuit Zandvoort", "country": "Netherlands", "type": "Technical", "length_km": 4.26, "corners": 14, "lat": 52.3888, "lon": 4.5409},
    {"id": "monza", "name": "Autodromo Nazionale Monza", "country": "Italy", "type": "Power", "length_km": 5.79, "corners": 11, "lat": 45.6156, "lon": 9.2811},
    {"id": "madring", "name": "Madrid In-Motion Ring", "country": "Spain", "type": "Balanced", "length_km": 5.47, "corners": 20, "lat": 40.4239, "lon": -3.59},
    {"id": "baku", "name": "Baku City Circuit", "country": "Azerbaijan", "type": "Street", "length_km": 6.00, "corners": 20, "lat": 40.3725, "lon": 49.8533},
    {"id": "marina-bay", "name": "Marina Bay Street Circuit", "country": "Singapore", "type": "Street", "length_km": 4.94, "corners": 19, "lat": 1.2914, "lon": 103.864},
    {"id": "suzuka", "name": "Suzuka International Racing Course", "country": "Japan", "type": "Technical", "length_km": 5.81, "corners": 18, "lat": 34.8431, "lon": 136.5407},
    {"id": "lusail", "name": "Lusail International Circuit", "country": "Qatar", "type": "High-Speed", "length_km": 5.38, "corners": 16, "lat": 25.49, "lon": 51.4542},
    {"id": "austin", "name": "Circuit of the Americas", "country": "USA", "type": "Mixed", "length_km": 5.51, "corners": 20, "lat": 30.1328, "lon": -97.6411},
    {"id": "mexico-city", "name": "Autodromo Hermanos Rodriguez", "country": "Mexico", "type": "Balanced", "length_km": 4.30, "corners": 17, "lat": 19.4042, "lon": -99.0907},
    {"id": "interlagos", "name": "Autodromo Jose Carlos Pace", "country": "Brazil", "type": "Mixed", "length_km": 4.31, "corners": 15, "lat": -23.7036, "lon": -46.6997},
    {"id": "las-vegas", "name": "Las Vegas Strip Circuit", "country": "USA", "type": "Power", "length_km": 6.20, "corners": 17, "lat": 36.1147, "lon": -115.1728},
    {"id": "yas-marina", "name": "Yas Marina Circuit", "country": "Abu Dhabi", "type": "Balanced", "length_km": 5.28, "corners": 16, "lat": 24.4672, "lon": 54.6031},
    {"id": "paul_ricard", "name": "Circuit Paul Ricard", "country": "France", "type": "Balanced", "length_km": 5.84, "corners": 15, "lat": 43.2506, "lon": 5.7917},
    {"id": "hockenheimring", "name": "Hockenheimring", "country": "Germany", "type": "Power", "length_km": 4.57, "corners": 17, "lat": 49.3278, "lon": 8.5658},
    {"id": "sochi", "name": "Sochi Autodrom", "country": "Russia", "type": "Balanced", "length_km": 5.84, "corners": 18, "lat": 43.4057, "lon": 39.9578},
    {"id": "mugello", "name": "Autodromo Internazionale del Mugello", "country": "Italy", "type": "High-Speed", "length_km": 5.25, "corners": 15, "lat": 43.9975, "lon": 11.3719},
    {"id": "nurburgring", "name": "Nürburgring", "country": "Germany", "type": "Technical", "length_km": 5.14, "corners": 16, "lat": 50.3356, "lon": 6.9475},
    {"id": "portimao", "name": "Autódromo Internacional do Algarve", "country": "Portugal", "type": "Mixed", "length_km": 4.65, "corners": 15, "lat": 37.2314, "lon": -8.6283},
    {"id": "istanbul", "name": "Intercity Istanbul Park", "country": "Turkey", "type": "Technical", "length_km": 5.34, "corners": 14, "lat": 40.9517, "lon": 29.4050},
]

_seen = set()
CIRCUITS = [c for c in CIRCUITS if not (c["id"] in _seen or _seen.add(c["id"]))]


EVENT_NAME_TO_CIRCUIT = {
    "bahrain": "bahrain",
    "sakhir": "bahrain",
    "saudi arabian": "jeddah",
    "chinese": "shanghai",
    "australian": "melbourne",
    "azerbaijan": "baku",
    "miami": "miami",
    "monaco": "monaco",
    "emilia romagna": "monza",
    "spanish": "catalunya",
    "barcelona": "catalunya",
    "canadian": "montreal",
    "austrian": "spielberg",
    "styrian": "spielberg",
    "british": "silverstone",
    "70th anniversary": "silverstone",
    "hungarian": "hungaroring",
    "belgian": "spa-francorchamps",
    "dutch": "zandvoort",
    "italian": "monza",
    "tuscan": "mugello",
    "eifel": "nurburgring",
    "madrid": "madring",
    "singapore": "marina-bay",
    "japanese": "suzuka",
    "qatar": "lusail",
    "united states": "austin",
    "mexico": "mexico-city",
    "mexican": "mexico-city",
    "brazilian": "interlagos",
    "sao paulo": "interlagos",
    "são paulo": "interlagos",
    "las vegas": "las-vegas",
    "abu dhabi": "yas-marina",
    "french": "paul_ricard",
    "german": "hockenheimring",
    "russian": "sochi",
    "portuguese": "portimao",
    "turkish": "istanbul",
}


def circuit_id_for_event(event_name):
    name = (event_name or "").lower()
    for key, circuit_id in EVENT_NAME_TO_CIRCUIT.items():
        if key in name:
            return circuit_id
    return None
