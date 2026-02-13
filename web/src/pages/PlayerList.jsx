import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, User } from 'lucide-react'

export default function PlayerList() {
    const [players, setPlayers] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/players')
            .then(res => res.json())
            .then(data => {
                setPlayers(data)
                setLoading(false)
            })
            .catch(err => {
                console.error(err)
                setLoading(false)
            })
    }, [])

    if (loading) {
        return (
            <div className="flex justify-center py-20">
                <Loader2 className="w-10 h-10 animate-spin text-[var(--accent)]" />
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <h2 className="text-3xl font-bold">Players</h2>

            <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-6">
                {players.map((player, i) => (
                    <Link
                        key={i}
                        to={`/players/${encodeURIComponent(player.url)}`}
                        className="glass-card p-4 hover:border-[var(--accent)]/50 transition-all flex items-center gap-4 group"
                    >
                        <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center p-2 text-[var(--text-secondary)]">
                            <User />
                        </div>
                        <div>
                            <h3 className="font-semibold group-hover:text-[var(--accent)] transition-colors line-clamp-1">{player.name}</h3>
                            <p className="text-sm text-[var(--text-secondary)] line-clamp-1">{player.team || player.role || 'Player'}</p>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    )
}
