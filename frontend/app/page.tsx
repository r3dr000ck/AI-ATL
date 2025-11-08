'use client';

import { useEffect, useState } from 'react';
import { apiClient, HealthStatus, PositionsResponse } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function DashboardPage() {
  const { user, logout, isAuthenticated } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [positions, setPositions] = useState<PositionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [animateNumbers, setAnimateNumbers] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [healthData, positionsData] = await Promise.all([
          apiClient.getHealth(),
          apiClient.getPositions(),
        ]);
        setHealth(healthData);
        setPositions(positionsData);
        setError(null);
        setAnimateNumbers(true);
        setTimeout(() => setAnimateNumbers(false), 300);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);

    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--background)]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-xl text-[var(--foreground)] font-medium">Initializing Trading System...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--background)]">
        <div className="glass-card p-8 rounded-2xl max-w-md">
          <div className="text-red-400 text-xl font-semibold mb-2">Connection Error</div>
          <div className="text-[var(--foreground-secondary)]">{error}</div>
          <div className="mt-4 text-sm text-[var(--foreground-secondary)]">
            Make sure the backend server is running on port 8000
          </div>
        </div>
      </div>
    );
  }

  const totalPnL = positions?.positions.reduce((sum, p) => sum + (p.pnl || 0), 0) || 0;

  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-8">
      {/* Animated background gradient */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 -right-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 md:mb-12 fade-in-up">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-2 gradient-text">
                ValueCell AI Trader
              </h1>
              <p className="text-[var(--foreground-secondary)] text-lg">
                LLM-Powered Algorithmic Trading Platform
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 px-4 py-2 glass-card rounded-full">
                <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-green-400 pulse-glow' : 'bg-red-400'}`}></div>
                <span className="text-sm font-medium">{health?.status === 'healthy' ? 'System Online' : 'System Offline'}</span>
              </div>

              {/* User Profile Menu */}
              {isAuthenticated && user && (
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-3 px-4 py-2 glass-card rounded-full hover:bg-blue-500/10 transition-all"
                  >
                    <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center text-black font-bold">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium">{user.name}</span>
                  </button>

                  {/* Dropdown Menu */}
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-56 glass-card rounded-xl p-2 shadow-2xl z-50">
                      <div className="px-3 py-2 border-b border-[var(--border-color)]">
                        <p className="text-sm font-semibold">{user.name}</p>
                        <p className="text-xs text-[var(--foreground-secondary)]">{user.email}</p>
                      </div>
                      <Link
                        href="/auth"
                        className="block px-3 py-2 text-sm hover:bg-blue-500/10 rounded-lg transition-colors mt-2"
                      >
                        Profile Settings
                      </Link>
                      <button
                        onClick={logout}
                        className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                      >
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Login Button if not authenticated */}
              {!isAuthenticated && (
                <Link
                  href="/auth"
                  className="px-5 py-2 bg-white text-black rounded-full font-semibold hover:bg-gray-200 transition-all"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8 md:mb-12">
          <MetricCard
            title="Available Capital"
            value={`$${health?.broker_capital.toFixed(2) || '0.00'}`}
            icon="💰"
            trend={null}
            animate={animateNumbers}
          />
          <MetricCard
            title="Active Positions"
            value={health?.num_positions.toString() || '0'}
            icon="📊"
            trend={null}
            animate={animateNumbers}
          />
          <MetricCard
            title="Total P&L"
            value={`$${totalPnL.toFixed(2)}`}
            icon={totalPnL >= 0 ? '📈' : '📉'}
            trend={totalPnL >= 0 ? 'up' : 'down'}
            animate={animateNumbers}
          />
          <MetricCard
            title="Events Cached"
            value={health?.num_events?.toString() || '0'}
            icon="🔔"
            trend={null}
            animate={animateNumbers}
          />
        </div>

        {/* Quick Actions */}
        <div className="glass-card rounded-2xl p-6 md:p-8 mb-8 fade-in-up">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <span className="text-3xl">⚡</span>
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <ActionButton
              href="/trades"
              title="Execute Trade"
              description="Open new positions"
              icon="🎯"
              color="blue"
            />
            <ActionButton
              href="/positions"
              title="Manage Positions"
              description="View & modify holdings"
              icon="💼"
              color="purple"
            />
            <ActionButton
              href="/analytics"
              title="View Analytics"
              description="Performance insights"
              icon="📊"
              color="green"
            />
          </div>
        </div>

        {/* Positions Table */}
        <div className="glass-card rounded-2xl p-6 md:p-8 fade-in-up">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <span className="text-3xl">💼</span>
            Current Positions
          </h2>
          {positions && positions.positions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--border-accent)]">
                    <th className="text-left py-4 px-4 text-[var(--foreground-secondary)] font-semibold text-sm">Ticker</th>
                    <th className="text-right py-4 px-4 text-[var(--foreground-secondary)] font-semibold text-sm">Quantity</th>
                    <th className="text-right py-4 px-4 text-[var(--foreground-secondary)] font-semibold text-sm">Entry</th>
                    <th className="text-right py-4 px-4 text-[var(--foreground-secondary)] font-semibold text-sm">Current</th>
                    <th className="text-right py-4 px-4 text-[var(--foreground-secondary)] font-semibold text-sm">P&L</th>
                    <th className="text-right py-4 px-4 text-[var(--foreground-secondary)] font-semibold text-sm">P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.positions.map((position: any) => {
                    const pnl = position.pnl || 0;
                    const pnlPct = position.pnl_pct || 0;
                    return (
                      <tr key={position.ticker} className="border-b border-[var(--border-color)] hover:bg-[var(--background-tertiary)] transition-colors">
                        <td className="py-4 px-4 font-bold text-lg">{position.ticker}</td>
                        <td className="text-right py-4 px-4">{position.quantity}</td>
                        <td className="text-right py-4 px-4 font-mono">${position.entry_price.toFixed(2)}</td>
                        <td className="text-right py-4 px-4 font-mono">
                          ${position.current_price?.toFixed(2) || '-'}
                        </td>
                        <td className={`text-right py-4 px-4 font-bold font-mono ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                        </td>
                        <td className={`text-right py-4 px-4 font-bold font-mono ${pnlPct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div className="mt-6 pt-4 border-t border-[var(--border-color)] flex justify-between items-center">
                <span className="text-[var(--foreground-secondary)]">Total Exposure</span>
                <span className="text-xl font-bold">${positions.total_exposure.toFixed(2)}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <p className="text-[var(--foreground-secondary)] text-lg">No active positions</p>
              <p className="text-sm text-[var(--foreground-secondary)] mt-2">Execute a trade to get started</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-[var(--foreground-secondary)] text-sm">
          <div className="flex items-center justify-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full pulse-glow"></div>
            <span>Last updated: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : '-'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Modern Metric Card Component
function MetricCard({ title, value, icon, trend, animate }: {
  title: string;
  value: string;
  icon: string;
  trend: 'up' | 'down' | null;
  animate: boolean;
}) {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
  };

  return (
    <div className="glass-card rounded-2xl p-6 hover:scale-105 transition-transform cursor-pointer">
      <div className="flex items-start justify-between mb-4">
        <div className="text-3xl">{icon}</div>
        {trend && (
          <div className={`text-sm font-semibold ${trendColors[trend]}`}>
            {trend === 'up' ? '↗' : '↘'}
          </div>
        )}
      </div>
      <div className="text-[var(--foreground-secondary)] text-sm mb-2">{title}</div>
      <div className={`text-3xl font-bold ${animate ? 'number-pop' : ''}`}>
        {value}
      </div>
    </div>
  );
}

// Action Button Component
function ActionButton({ href, title, description, icon, color }: {
  href: string;
  title: string;
  description: string;
  icon: string;
  color: 'blue' | 'purple' | 'green';
}) {
  const colorClasses = {
    blue: 'hover:border-blue-500/50 hover:bg-blue-500/10',
    purple: 'hover:border-purple-500/50 hover:bg-purple-500/10',
    green: 'hover:border-green-500/50 hover:bg-green-500/10',
  };

  return (
    <a
      href={href}
      className={`block p-6 rounded-xl border border-[var(--border-color)] ${colorClasses[color]} transition-all hover:scale-105 cursor-pointer`}
    >
      <div className="text-3xl mb-3">{icon}</div>
      <div className="font-bold text-lg mb-1">{title}</div>
      <div className="text-sm text-[var(--foreground-secondary)]">{description}</div>
    </a>
  );
}
