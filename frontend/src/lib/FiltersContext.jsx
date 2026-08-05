import { createContext, useContext, useEffect, useState } from 'react';
import { api } from './api';

const FiltersContext = createContext(null);

const SEASONS = [2021, 2022, 2023, 2024, 2025, 2026];
const METRIC_FOCUS = ['Overall', 'Braking', 'Traction', 'Apex Speed', 'Tyre Mgmt', 'Aero Sens.', 'Technical'];
const SESSIONS = ['Qualifying', 'Race'];

export function FiltersProvider({ children }) {
  const [teams, setTeams] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [circuits, setCircuits] = useState([]);
  const [loading, setLoading] = useState(true);

  const [teamId, setTeamId] = useState('redbull');
  const [driverId, setDriverId] = useState('VER');
  const [driverBId, setDriverBId] = useState('HAM'); // for head-to-head
  const [circuitId, setCircuitId] = useState('monza');
  const [trackType, setTrackType] = useState('All');
  const [season, setSeason] = useState('2026');
  const [metricFocus, setMetricFocus] = useState('Overall');
  const [session, setSession] = useState('Qualifying');

  useEffect(() => {
    Promise.all([api.teams(), api.drivers(), api.circuits()])
      .then(([t, d, c]) => { setTeams(t.teams); setDrivers(d.drivers); setCircuits(c.circuits); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const team = teams.find(t => t.id === teamId) || teams[0];
  const driver = drivers.find(d => d.id === driverId) || drivers[0];
  const trackTypes = ['All', ...Array.from(new Set(circuits.map(c => c.type)))];
  const filteredCircuits = trackType === 'All' ? circuits : circuits.filter(c => c.type === trackType);
  const circuit = filteredCircuits.find(c => c.id === circuitId) || filteredCircuits[0];

  const value = {
    loading, teams, drivers, circuits, trackTypes, filteredCircuits, SEASONS, METRIC_FOCUS, SESSIONS,
    teamId, setTeamId, driverId, setDriverId, driverBId, setDriverBId,
    circuitId, setCircuitId, trackType, setTrackType, season, setSeason,
    metricFocus, setMetricFocus, session, setSession,
    team, driver, circuit,
  };
  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters() {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error('useFilters must be used inside FiltersProvider');
  return ctx;
}
