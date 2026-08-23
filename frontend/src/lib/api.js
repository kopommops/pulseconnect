
const BASE = `${import.meta.env.VITE_API_BASE_URL || ''}/api`;

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  drivers: () => get('/drivers'),
  driver: (id) => get(`/drivers/${id}`),
  driverInsights: (id) => get(`/drivers/${id}/insights`),
  teams: () => get('/teams'),
  team: (id) => get(`/teams/${id}`),
  circuits: () => get('/circuits'),
  circuit: (id) => get(`/circuits/${id}`),
  compatibility: (driverId, circuitId) => get(`/compatibility/${driverId}/${circuitId}`),
  consistency: (season) => get(`/consistency/${season}`),
  trackDna: (circuitId) => get(`/track-dna/${circuitId}`),
  headToHead: (a, b, season = '2026') => get(`/head-to-head/${a}/${b}?season=${season}`),
  standings: (season) => get(`/standings/${season}`),
  nextRace: (season = 2026) => get(`/race-day/next?season=${season}`),
  raceRoster: (season, round) => get(`/race-day/${season}/${round}/roster`),
  racePredictions: (season, round) => get(`/race-day/${season}/${round}/predictions`),
  raceActual: (season, round) => get(`/race-day/${season}/${round}/actual`),
  simulateStrategy: (season, round, body) =>
    fetch(`${BASE}/strategy/${season}/${round}/simulate-strategy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then((res) => {
      if (!res.ok) throw new Error(`API simulate-strategy failed: ${res.status}`);
      return res.json();
    }),
};