import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import Brain from './pages/Brain'
import Energy from './pages/Energy'
import Devices from './pages/Devices'
import Safety from './pages/Safety'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout><Overview /></Layout>} />
      <Route path="/brain" element={<Layout><Brain /></Layout>} />
      <Route path="/energy" element={<Layout><Energy /></Layout>} />
      <Route path="/devices" element={<Layout><Devices /></Layout>} />
      <Route path="/safety" element={<Layout><Safety /></Layout>} />
    </Routes>
  )
}