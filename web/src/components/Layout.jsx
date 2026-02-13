import { Link, Outlet } from 'react-router-dom'
import { Crown, Search, Menu } from 'lucide-react'

export default function Layout() {
    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
            <nav className="border-b border-[var(--glass-border)] bg-[var(--bg-secondary)]/50 backdrop-blur-md sticky top-0 z-50">
                <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2 text-xl font-bold bg-gradient-to-r from-white to-[var(--text-secondary)] bg-clip-text text-transparent">
                        <Crown className="w-6 h-6 text-[var(--accent)]" />
                        <span>Volleybox<span className="text-[var(--accent)]">Pro</span></span>
                    </Link>

                    <div className="flex items-center gap-6 text-[var(--text-secondary)]">
                        <Link to="/teams" className="hover:text-[var(--accent)] transition-colors">Teams</Link>
                        <Link to="/players" className="hover:text-[var(--accent)] transition-colors">Players</Link>
                        <Link to="/tournaments" className="hover:text-[var(--accent)] transition-colors">Tournaments</Link>
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="p-2 hover:bg-white/5 rounded-full transition-colors">
                            <Search className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </nav>

            <main className="container mx-auto px-4 py-8">
                <Outlet />
            </main>
        </div>
    )
}
