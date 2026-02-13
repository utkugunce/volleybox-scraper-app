import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

export default function TeamList() {
    const [teams, setTeams] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/teams')
            .then(res => res.json())
            .then(data => {
                setTeams(data)
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
            <h2 className="text-3xl font-bold">Teams</h2>

            <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-6">
                {teams.map((team, i) => (
                    <Link
                        key={i}
                        to={`/teams/${encodeURIComponent(team.url)}`}
                        className="glass-card p-4 hover:border-[var(--accent)]/50 transition-all flex items-center gap-4 group"
                    >
                        <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center p-2">
                            {team.logo_url ? (
                                <img src={team.logo_url} alt={team.name} className="w-full h-full object-contain" />
                            ) : (
                                <span className="text-xl font-bold text-[var(--text-secondary)]">{team.name[0]}</span>
                            )}
                        </div>
                        <div>
                            <h3 className="font-semibold group-hover:text-[var(--accent)] transition-colors line-clamp-1">{team.name}</h3>
                            <p className="text-sm text-[var(--text-secondary)] line-clamp-1">{team.country}</p>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    )
}
