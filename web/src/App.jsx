import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import TeamList from './pages/TeamList'
import TeamDetail from './pages/TeamDetail'
import PlayerList from './pages/PlayerList'
import TournamentList from './pages/TournamentList'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="teams" element={<TeamList />} />
          <Route path="teams/:id" element={<TeamDetail />} />
          <Route path="players" element={<PlayerList />} />
          <Route path="tournaments" element={<TournamentList />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
