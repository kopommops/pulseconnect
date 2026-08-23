import { useEffect, useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import TopBar from './components/TopBar';
import Landing from './pages/Landing';
import DashboardLayout from './pages/DashboardLayout';
import DriverProfile from './pages/DriverProfile';
import Compatibility from './pages/Compatibility';
import Consistency from './pages/Consistency';
import TrackDNA from './pages/TrackDNA';
import HeadToHead from './pages/HeadToHead';
import RaceDay from './pages/RaceDay';
import { FiltersProvider } from './lib/FiltersContext';

export default function App() {
  const [theme, setTheme] = useState('dark');
  useEffect(() => { document.body.classList.toggle('light', theme === 'light'); }, [theme]);

  return (
    <FiltersProvider>
      <TopBar theme={theme} toggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route path="profile" element={<DriverProfile />} />
          <Route path="compatibility" element={<Compatibility />} />
          <Route path="consistency" element={<Consistency />} />
          <Route path="track-dna" element={<TrackDNA />} />
          <Route path="head-to-head" element={<HeadToHead />} />
        </Route>
        <Route path="/race-day" element={<RaceDay />} />
      </Routes>
    </FiltersProvider>
  );
}
