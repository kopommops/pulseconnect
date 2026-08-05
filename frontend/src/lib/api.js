
const BASE = '/api';

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
};
