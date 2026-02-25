import { Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import SkillPage from './pages/SkillPage'
import VerifyPage from './pages/VerifyPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/skill" element={<SkillPage />} />
      <Route path="/verify" element={<VerifyPage />} />
    </Routes>
  )
}
