import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2, MapPin, Calendar, Globe } from 'lucide-react'

export default function TeamDetail() {
    const { id } = useParams()
    const [team, setTeam] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch(`/api/teams/detail?url=${encodeURIComponent(id)}`)
            .then(res => res.json())
            .then(data => {
                setTeam(data)
                setLoading(false)
            })
            .catch(err => {
                console.error(err)
                setLoading(false)
            })
    }, [id])

    if (loading) {
        return (
            <div className="flex justify-center py-20">
                <Loader2 className="w-10 h-10 animate-spin text-[var(--accent)]" />
            </div>
        )
    }

    if (!team) return <div>Team not found</div>

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div className="glass-card p-8 flex items-center gap-8 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent)]/10 blur-[50px] rounded-full" />

                <div className="w-32 h-32 bg-white/5 rounded-2xl flex items-center justify-center p-4 z-10">
                    {team.logo_url ? (
                        <img src={team.logo_url} alt={team.name} className="w-full h-full object-contain" />
                    ) : (
                        <span className="text-4xl font-bold">{team.name[0]}</span>
                    )}
                </div>

                <div className="z-10 space-y-2">
                    <h1 className="text-4xl font-bold">{team.name}</h1>
                    <div className="flex items-center gap-6 text-[var(--text-secondary)]">
                        {team.country && <span className="flex items-center gap-2"><Globe className="w-4 h-4" /> {team.country}</span>}
                        {team.founded && <span className="flex items-center gap-2"><Calendar className="w-4 h-4" /> Founded {team.founded}</span>}
                        {team.home && <span className="flex items-center gap-2"><MapPin className="w-4 h-4" /> {team.home}</span>}
                    </div>
                </div>
            </div>

            {/* Roster */}
            <div className="glass-card p-6">
                <h2 className="text-2xl font-bold mb-6">Current Roster</h2>

                {team.roster && team.roster.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left border-b border-[var(--glass-border)]">
                                    <th className="pb-4 pl-4 text-[var(--text-secondary)] font-medium">#</th>
                                    <th className="pb-4 text-[var(--text-secondary)] font-medium">Player</th>
                                    <th className="pb-4 text-[var(--text-secondary)] font-medium">Position</th>
                                    <th className="pb-4 text-[var(--text-secondary)] font-medium">Height</th>
                                    <th className="pb-4 text-[var(--text-secondary)] font-medium">Age</th>
                                </tr>
                            </thead>
                            <tbody>
                                {team.roster.map((player, i) => (
                                    <tr key={i} className="border-b border-[var(--glass-border)] hover:bg-white/5 transition-colors">
                                        <td className="py-4 pl-4 font-mono text-[var(--accent)]">{player.number || '-'}</td>
                                        <td className="py-4 font-medium">{player.name}</td>
                                        <td className="py-4 text-[var(--text-secondary)]">{player.position}</td>
                                        <td className="py-4 text-[var(--text-secondary)]">{player.height}</td>
                                        <td className="py-4 text-[var(--text-secondary)]">{player.age}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-[var(--text-secondary)]">No roster data available.</p>
                )}
            </div>
        </div>
    )
}
