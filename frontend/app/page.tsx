'use client';

import { useEffect, useState } from 'react';
import { apiClient, HealthStatus, PositionsResponse } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';
import dynamic from 'next/dynamic';

// Dynamically import Dither to avoid SSR issues with Three.js
const Dither = dynamic(() => import('@/components/Dither'), {
  ssr: false,
  loading: () => null
});

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
<<<<<<< HEAD
    <div className="relative min-h-screen bg-gray-950 text-white overflow-hidden">
      {/* Animated background pattern */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        {/* soft gradient blobs */}
        <div className="absolute -top-32 -left-24 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-float-slow" />
        <div className="absolute -bottom-40 -right-24 w-96 h-96 bg-purple-500/25 rounded-full blur-3xl animate-float-medium" />
        {/* subtle grid overlay */}
        <div className="h-full w-full opacity-20 bg-[radial-gradient(circle_at_top,_#1f2933_0,_transparent_60%),linear-gradient(to_right,_rgba(148,163,184,0.15)_1px,_transparent_1px),linear-gradient(to_bottom,_rgba(148,163,184,0.1)_1px,_transparent_1px)] bg-[size:400px_400px,64px_64px,64px_64px] animate-slow-pan" />
      </div>

      {/* Foreground content */}
      <div className="relative z-10 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">ValueCell AI Trader</h1>
            <p className="text-gray-400">Real-time algorithmic trading dashboard</p>
=======
    <div className="min-h-screen bg-background text-foreground p-4 md:p-8">
      {/* Dithered Waves Background */}
      <Dither
        waveSpeed={0.03}
        waveFrequency={2.5}
        waveAmplitude={0.35}
        waveColor={[0.2, 0.3, 0.5]}
        colorNum={6}
        pixelSize={3}
        disableAnimation={false}
        enableMouseInteraction={true}
        mouseRadius={0.8}
      />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8 md:mb-12 fade-in-up">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-2 gradient-text">
                Futures AI Trader
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
>>>>>>> d0ae0d8b4d189182f0c89ac010d1daf7deab1dc6
          </div>

<<<<<<< HEAD
<<<<<<< HEAD
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <StatusCard
              title="System Status"
              value={health?.status || 'Unknown'}
              color={health?.status === 'healthy' ? 'green' : 'red'}
            />
            <StatusCard
              title="Available Capital"
              value={`$${health?.broker_capital.toFixed(2) || '0.00'}`}
              color="blue"
            />
            <StatusCard
              title="Active Positions"
              value={health?.num_positions.toString() || '0'}
              color="purple"
            />
            <StatusCard
              title="Total P&L"
              value={`$${totalPnL.toFixed(2)}`}
              color={totalPnL >= 0 ? 'green' : 'red'}
            />
          </div>

          <div className="bg-gray-800 rounded-lg shadow-xl p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Quick Actions</h2>
            <div className="flex gap-4 flex-wrap">
              <Link
                href="/trades"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
              >
                Execute Trade
              </Link>
              <Link
                href="/positions"
                className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition font-medium"
              >
                Manage Positions
              </Link>
              <button className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium">
                View Analytics
              </button>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg shadow-xl p-6">
            <h2 className="text-2xl font-semibold mb-4">Current Positions</h2>
            {positions && positions.positions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4 text-gray-400">Ticker</th>
                      <th className="text-right py-3 px-4 text-gray-400">Quantity</th>
                      <th className="text-right py-3 px-4 text-gray-400">Entry Price</th>
                      <th className="text-right py-3 px-4 text-gray-400">Current Price</th>
                      <th className="text-right py-3 px-4 text-gray-400">P&L</th>
                      <th className="text-right py-3 px-4 text-gray-400">P&L %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.positions.map((position) => {
                      const pnl = position.pnl || 0;
                      const pnlPct = position.pnl_pct || 0;
                      return (
                        <tr key={position.ticker} className="border-b border-gray-700 hover:bg-gray-750">
                          <td className="py-3 px-4 font-semibold">{position.ticker}</td>
                          <td className="text-right py-3 px-4">{position.quantity}</td>
                          <td className="text-right py-3 px-4">${position.entry_price.toFixed(2)}</td>
                          <td className="text-right py-3 px-4">
                            ${position.current_price?.toFixed(2) || '-'}
                          </td>
                          <td className={`text-right py-3 px-4 font-semibold ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            ${pnl.toFixed(2)}
                          </td>
                          <td className={`text-right py-3 px-4 font-semibold ${pnlPct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {pnlPct.toFixed(2)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <div className="mt-4 text-right text-gray-400">
                  Total Exposure: ${positions.total_exposure.toFixed(2)}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No active positions</p>
            )}
          </div>

          <div className="mt-4 text-center text-gray-500 text-sm">
            Last updated: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : '-'} | Events cached: {health?.num_events || 0}
=======
=======
>>>>>>> 23f2be57215fb59c814f1ee515aef881af82971b
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

<<<<<<< HEAD
=======
        {/* Market Overview */}
        <div className="glass-card rounded-2xl p-6 md:p-8 mb-8 fade-in-up">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <span className="text-3xl">📈</span>
              Market Overview
            </h2>
            <span className="text-xs md:text-sm text-[var(--foreground-secondary)]">
              Simulated intraday movement
            </span>
          </div>

          <div className="relative h-32 md:h-40 overflow-hidden rounded-xl bg-[var(--background-secondary)] border border-[var(--border-color)] px-4 py-3 flex items-end gap-1">
            {Array.from({ length: 40 }).map((_, idx) => {
              const height =
                40 + Math.sin(idx / 2) * 20 + (idx % 5) * 4;
              const clampedHeight = Math.max(10, Math.min(90, height));
              const opacity = 0.4 + (idx % 5) * 0.1;

              return (
                <div
                  key={idx}
                  className="flex-1 bg-gradient-to-t from-blue-500/40 to-purple-400/70 rounded-t-full"
                  style={{
                    height: `${clampedHeight}%`,
                    opacity,
                  }}
                />
              );
            })}
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[var(--background)]/80 via-transparent" />
          </div>

          <p className="mt-4 text-xs md:text-sm text-[var(--foreground-secondary)]">
            Intraday equity curve, scaled from recent P&amp;L for visualization.
          </p>
        </div>

>>>>>>> 23f2be57215fb59c814f1ee515aef881af82971b
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
>>>>>>> d0ae0d8b4d189182f0c89ac010d1daf7deab1dc6
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
<<<<<<< HEAD
=======

// Table Skeleton Component for loading state
function TableSkeleton() {
  return (
    <div className="animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="flex gap-4 p-4 border-b border-[var(--border-color)] items-center"
        >
          <div className="h-4 bg-[var(--background-secondary)] rounded w-20" />
          <div className="h-4 bg-[var(--background-secondary)] rounded flex-1" />
          <div className="h-4 bg-[var(--background-secondary)] rounded w-24" />
          <div className="h-4 bg-[var(--background-secondary)] rounded w-24" />
          <div className="h-4 bg-[var(--background-secondary)] rounded w-24" />
          <div className="h-4 bg-[var(--background-secondary)] rounded w-24" />
        </div>
      ))}
    </div>
  );
}
>>>>>>> 23f2be57215fb59c814f1ee515aef881af82971b
