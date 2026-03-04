import { Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Arena from './pages/Arena'
import DebatePage from './pages/DebatePage'
import SkillPage from './pages/SkillPage'
import VerifyPage from './pages/VerifyPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/arena" element={<Arena />} />
      <Route path="/arena/rounds/:roundId" element={<DebatePage />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/skill" element={<SkillPage />} />
      <Route path="/verify" element={<VerifyPage />} />
    </Routes>
  )
}
