import { Link } from 'react-router-dom'
import { Users, Trophy, User } from 'lucide-react'

export default function Home() {
    return (
        <div className="space-y-12 animate-fade-in">
            <div className="text-center space-y-4 py-16">
                <h1 className="text-5xl font-bold bg-gradient-to-r from-white to-[var(--text-secondary)] bg-clip-text text-transparent">
                    Professional Volleyball Data
                </h1>
                <p className="text-[var(--text-secondary)] text-xl max-w-2xl mx-auto">
                    Access comprehensive data from women.volleybox.net with a premium interface.
                </p>

                <div className="max-w-xl mx-auto mt-8 relative">
                    <input
                        type="text"
                        placeholder="Search for teams, players, tournaments..."
                        className="w-full pl-12 pr-4 py-4 rounded-xl bg-white/5 border border-[var(--glass-border)] focus:border-[var(--accent)] outline-none text-lg transition-all"
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <FeatureCard
                    to="/teams"
                    icon={<Users className="w-8 h-8 text-blue-400" />}
                    title="Teams"
                    desc="Browse clubs from around the world"
                />
                <FeatureCard
                    to="/players"
                    icon={<User className="w-8 h-8 text-pink-400" />}
                    title="Players"
                    desc="Detailed profiles and statistics"
                />
                <FeatureCard
                    to="/tournaments"
                    icon={<Trophy className="w-8 h-8 text-yellow-400" />}
                    title="Tournaments"
                    desc="League standings and match results"
                />
            </div>
        </div>
    )
}

function FeatureCard({ to, icon, title, desc }) {
    return (
        <Link to={to} className="group glass-card p-6 hover:border-[var(--accent)]/50 transition-all hover:transform hover:-translate-y-1 block">
            <div className="mb-4 p-3 bg-white/5 rounded-lg w-fit group-hover:bg-[var(--accent)]/20 transition-colors">
                {icon}
            </div>
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-[var(--text-secondary)]">{desc}</p>
        </Link>
    )
}
