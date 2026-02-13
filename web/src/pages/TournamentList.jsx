import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, Trophy } from 'lucide-react'

export default function TournamentList() {
    const [tournaments, setTournaments] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/tournaments')
            .then(res => res.json())
            .then(data => {
                setTournaments(data)
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
            <h2 className="text-3xl font-bold">Tournaments</h2>

            <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-6">
                {tournaments.map((t, i) => (
                    <Link
                        key={i}
                        to={`/tournaments/${encodeURIComponent(t.url)}`}
                        className="glass-card p-4 hover:border-[var(--accent)]/50 transition-all flex items-center gap-4 group"
                    >
                        <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center p-2 text-[var(--text-secondary)]">
                            <Trophy />
                        </div>
                        <div>
                            <h3 className="font-semibold group-hover:text-[var(--accent)] transition-colors line-clamp-1">{t.name}</h3>
                            <p className="text-sm text-[var(--text-secondary)] line-clamp-1">{t.season || '2025/26'}</p>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    )
}
