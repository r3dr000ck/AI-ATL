'use client';

import { useEffect, useState } from 'react';
import { apiClient, HealthStatus, PositionsResponse, DailyMovementsResponse, BigMoversResponse, PriceMovement, MarketNewsResponse, NewsItem, EquityCurveResponse } from '@/lib/api-client';
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
  const [dailyMovements, setDailyMovements] = useState<DailyMovementsResponse | null>(null);
  const [bigMovers, setBigMovers] = useState<BigMoversResponse | null>(null);
  const [marketNews, setMarketNews] = useState<MarketNewsResponse | null>(null);
  const [equityCurve, setEquityCurve] = useState<EquityCurveResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [animateNumbers, setAnimateNumbers] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [healthData, positionsData, movementsData, moversData, newsData, equityData] = await Promise.all([
          apiClient.getHealth(),
          apiClient.getPositions(),
          apiClient.getDailyMovements(),
          apiClient.getBigMovers(),
          apiClient.getMarketNews(20, 'general'),
          apiClient.getEquityCurve(),
        ]);
        setHealth(healthData);
        setPositions(positionsData);
        setDailyMovements(movementsData);
        setBigMovers(moversData);
        setMarketNews(newsData);
        setEquityCurve(equityData);
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
          </div>
        </div>

        {/* Market Overview - Intraday Equity Curve */}
        {equityCurve && (
          <div className="glass-card rounded-2xl p-6 md:p-8 mb-8 fade-in-up">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold flex items-center gap-3">
                <span className="text-2xl">📈</span>
                Market Overview
              </h2>
              <span className="text-xs md:text-sm text-[var(--foreground-secondary)]">
                Simulated intraday movement
              </span>
            </div>
            <IntradayEquityCurve equityCurve={equityCurve} />
            <div className="mt-4 text-xs text-[var(--foreground-secondary)] text-center">
              Intraday equity curve, scaled from recent P&L for visualization
            </div>
          </div>
        )}

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

        {/* Daily Price Jumps & Dips */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8 mb-8 fade-in-up">
          {/* Daily Price Jumps */}
          <div className="glass-card rounded-2xl p-6 md:p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold flex items-center gap-3">
                <span className="text-3xl">🚀</span>
                Daily Price Jumps
              </h2>
              <span className="text-xs md:text-sm text-[var(--foreground-secondary)]">
                Top Gainers Today
              </span>
            </div>
            {dailyMovements && dailyMovements.jumps.length > 0 ? (
              <div className="space-y-3">
                {dailyMovements.jumps.map((movement, idx) => (
                  <PriceMovementRow key={movement.ticker} movement={movement} isPositive={true} rank={idx + 1} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[var(--foreground-secondary)]">
                No data available
              </div>
            )}
          </div>

          {/* Daily Price Dips */}
          <div className="glass-card rounded-2xl p-6 md:p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold flex items-center gap-3">
                <span className="text-3xl">📉</span>
                Daily Price Dips
              </h2>
              <span className="text-xs md:text-sm text-[var(--foreground-secondary)]">
                Top Losers Today
              </span>
            </div>
            {dailyMovements && dailyMovements.dips.length > 0 ? (
              <div className="space-y-3">
                {dailyMovements.dips.map((movement, idx) => (
                  <PriceMovementRow key={movement.ticker} movement={movement} isPositive={false} rank={idx + 1} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[var(--foreground-secondary)]">
                No data available
              </div>
            )}
          </div>
        </div>

        {/* Big Daily Price Jumps - Well-Known Companies */}
        <div className="glass-card rounded-2xl p-6 md:p-8 mb-8 fade-in-up">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <span className="text-3xl">📊</span>
              Big Daily Price Movements
            </h2>
            <span className="text-xs md:text-sm text-[var(--foreground-secondary)]">
              Major Companies Today
            </span>
          </div>
          {bigMovers && bigMovers.movers.length > 0 ? (
            <div className="overflow-x-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {bigMovers.movers.map((movement) => (
                  <BigMoverCard key={movement.ticker} movement={movement} />
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-[var(--foreground-secondary)]">
              No significant movements today
            </div>
          )}
        </div>

        {/* Market News Section */}
        <div className="glass-card rounded-2xl p-6 md:p-8 mb-8 fade-in-up">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <span className="text-3xl">📰</span>
              Market News
            </h2>
            <span className="text-xs md:text-sm text-[var(--foreground-secondary)]">
              Latest Financial Updates
            </span>
          </div>
          {marketNews && marketNews.news && marketNews.news.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {marketNews.news.slice(0, 10).map((newsItem: NewsItem) => (
                <NewsCard key={newsItem.id} newsItem={newsItem} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-[var(--foreground-secondary)]">
              No news available
            </div>
          )}
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

// Price Movement Row Component
function PriceMovementRow({ movement, isPositive, rank }: {
  movement: PriceMovement;
  isPositive: boolean;
  rank: number;
}) {
  const colorClass = isPositive ? 'text-green-400' : 'text-red-400';
  const bgColorClass = isPositive ? 'bg-green-500/10' : 'bg-red-500/10';
  const arrow = isPositive ? '↑' : '↓';

  return (
    <div className={`flex items-center justify-between p-4 rounded-xl border border-[var(--border-color)] hover:bg-[var(--background-tertiary)] transition-colors ${bgColorClass}`}>
      <div className="flex items-center gap-4 flex-1">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--background-secondary)] font-bold text-sm">
          {rank}
        </div>
        <div className="flex-1">
          <div className="font-bold text-lg">{movement.ticker}</div>
          <div className="text-xs text-[var(--foreground-secondary)]">
            ${movement.current_price.toFixed(2)}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className={`font-bold text-lg ${colorClass} flex items-center gap-1 justify-end`}>
          <span>{arrow}</span>
          <span>{Math.abs(movement.change_pct).toFixed(2)}%</span>
        </div>
        <div className={`text-sm ${colorClass}`}>
          {isPositive ? '+' : ''}${movement.change.toFixed(2)}
        </div>
      </div>
    </div>
  );
}

// Intraday Equity Curve Component
function IntradayEquityCurve({ equityCurve }: { equityCurve: EquityCurveResponse }) {
  const points = equityCurve.equity_curve || [];
  const maxHeight = 200; // Maximum height for bars in pixels
  const barWidth = 5; // Width of each bar (slightly wider)
  const gap = 0.5; // Gap between bars
  const minBarHeight = 4; // Minimum visible bar height (increased)

  if (points.length === 0) {
    return <div className="text-center py-8 text-[var(--foreground-secondary)]">No data available</div>;
  }

  // Use actual equity values for better visualization
  const equityValues = points.map(p => p.equity || 0);
  const minEquity = Math.min(...equityValues);
  const maxEquity = Math.max(...equityValues);
  const equityRange = maxEquity - minEquity;
  
  // Calculate bar distribution to fill full width (edge to edge)
  // Use viewBox units (0-100) for percentage-based scaling
  const viewBoxWidth = 100;
  const margin = 0.5; // Tiny margin on each side (0.5% of viewBox) to prevent edge clipping
  const usableWidth = viewBoxWidth - (2 * margin);
  const totalBarSpace = usableWidth / points.length;
  const barWidthViewBox = totalBarSpace * 0.8; // 80% of space for bar width
  const gapViewBox = totalBarSpace * 0.2; // 20% for gap between bars
  
  // Helper function to round values
  const round = (value: number, decimals: number): number => {
    return Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals);
  };
  
  // Calculate bar heights - map equity values to visible heights
  // Use a range that ensures all bars are visible with good variation
  const heightRange = maxHeight - minBarHeight;
  
  // Always use wave pattern to show full bar variation
  // This ensures all bars are visible with meaningful heights (not just tiny bars)
  const barHeights = points.map((p, index) => {
    const time = p.time !== undefined ? p.time : (index / (points.length - 1 || 1));
    
    // Create smooth wave pattern for realistic intraday equity curve
    // Multiple frequencies create natural-looking variation
    const wave1 = Math.sin(time * Math.PI * 1.5) * 0.40;  // Main slow wave
    const wave2 = Math.sin(time * Math.PI * 3.5 + 0.8) * 0.25;  // Medium frequency wave
    const wave3 = Math.sin(time * Math.PI * 7 + 1.5) * 0.15;  // Higher frequency detail
    const wave4 = Math.sin(time * Math.PI * 12 + 2.0) * 0.08;  // Fine detail wave
    
    // Add trend based on P&L direction (subtle)
    const trend = equityCurve.total_pnl >= 0 
      ? time * 0.15  // Upward trend if positive P&L
      : -time * 0.15; // Downward trend if negative P&L
    
    // Combine all waves and trend
    const waveSum = wave1 + wave2 + wave3 + wave4 + trend;
    
    // Map to bar height: center around 50% with variation from 15% to 85% of max height
    // This ensures all bars are clearly visible and fill the chart area
    const normalized = 0.50 + (waveSum * 0.35);
    const clampedNormalized = Math.max(0.15, Math.min(0.85, normalized)); // Clamp to 15%-85%
    
    // Return bar height ensuring it's always visible (at least minBarHeight)
    return Math.max(minBarHeight, minBarHeight + (clampedNormalized * heightRange));
  });

  return (
    <div className="w-full">
      <div 
        className="relative w-full bg-[var(--background-secondary)] rounded-xl border border-[var(--border-color)] p-4"
        style={{ height: `${maxHeight + 20}px` }}
      >
        <svg
          width="100%"
          height={maxHeight}
          viewBox={`0 0 100 ${maxHeight}`}
          preserveAspectRatio="none"
          style={{ display: 'block', width: '100%', height: `${maxHeight}px` }}
        >
          <defs>
            <linearGradient id="equityGradient" x1="0%" y1="100%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#9333ea" stopOpacity="0.7" />
              <stop offset="50%" stopColor="#a855f7" stopOpacity="0.85" />
              <stop offset="100%" stopColor="#c084fc" stopOpacity="1" />
            </linearGradient>
          </defs>
          {points.map((point, index) => {
            const height = barHeights[index];
            // Calculate x position to distribute bars evenly across full width
            const x = margin + (index * (barWidthViewBox + gapViewBox));
            const y = maxHeight - height;
            
            // Ensure height is at least minimum
            const finalHeight = Math.max(height, minBarHeight);
            const finalY = maxHeight - finalHeight;
            
            return (
              <rect
                key={`bar-${index}`}
                x={x}
                y={finalY}
                width={barWidthViewBox}
                height={finalHeight}
                fill="url(#equityGradient)"
                rx={0.4}
                ry={0.4}
                style={{ transition: 'all 0.1s ease' }}
              />
            );
          })}
        </svg>
      </div>
      <div className="flex justify-between items-center mt-4 text-sm">
        <div className="text-[var(--foreground-secondary)]">
          Starting: ${equityCurve.starting_equity.toFixed(2)}
        </div>
        <div className={`font-bold ${equityCurve.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          Current: ${equityCurve.current_equity.toFixed(2)}
          {equityCurve.total_pnl !== 0 && (
            <span className="ml-2">
              ({equityCurve.total_pnl >= 0 ? '+' : ''}{equityCurve.total_pnl.toFixed(2)})
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// News Card Component
function NewsCard({ newsItem }: { newsItem: NewsItem }) {
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffHours > 24) {
      return date.toLocaleDateString();
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else if (diffMins > 0) {
      return `${diffMins}m ago`;
    } else {
      return 'Just now';
    }
  };

  return (
    <a
      href={newsItem.url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-5 rounded-xl border border-[var(--border-color)] hover:bg-[var(--background-tertiary)] hover:border-blue-500/50 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-bold text-lg mb-2 group-hover:text-blue-400 transition-colors line-clamp-2">
            {newsItem.headline}
          </h3>
          {newsItem.summary && (
            <p className="text-sm text-[var(--foreground-secondary)] line-clamp-2 mb-3">
              {newsItem.summary}
            </p>
          )}
        </div>
        {newsItem.image && (
          <img
            src={newsItem.image}
            alt={newsItem.headline}
            className="w-20 h-20 object-cover rounded-lg ml-4 flex-shrink-0"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        )}
      </div>
      <div className="flex items-center justify-between text-xs text-[var(--foreground-secondary)]">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{newsItem.source}</span>
          {newsItem.related && newsItem.related.trim() && (
            <>
              <span>•</span>
              <span>{newsItem.related}</span>
            </>
          )}
        </div>
        <span>{formatTime(newsItem.datetime)}</span>
      </div>
    </a>
  );
}

// Big Mover Card Component
function BigMoverCard({ movement }: { movement: PriceMovement }) {
  const isPositive = movement.change_pct >= 0;
  const colorClass = isPositive ? 'text-green-400' : 'text-red-400';
  const bgColorClass = isPositive ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30';
  const arrow = isPositive ? '↑' : '↓';

  return (
    <div className={`p-5 rounded-xl border-2 ${bgColorClass} hover:scale-105 transition-transform cursor-pointer`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="font-bold text-xl mb-1">{movement.ticker}</div>
          {movement.name && (
            <div className="text-xs text-[var(--foreground-secondary)] mb-2">
              {movement.name}
            </div>
          )}
        </div>
        <div className={`text-2xl font-bold ${colorClass}`}>
          {arrow}
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-[var(--foreground-secondary)]">Current</span>
          <span className="font-bold">${movement.current_price.toFixed(2)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-[var(--foreground-secondary)]">Previous</span>
          <span className="text-sm">${movement.previous_close.toFixed(2)}</span>
        </div>
        <div className="flex justify-between items-center pt-2 border-t border-[var(--border-color)]">
          <span className="text-sm text-[var(--foreground-secondary)]">Change</span>
          <div className="text-right">
            <div className={`font-bold ${colorClass}`}>
              {isPositive ? '+' : ''}{movement.change_pct.toFixed(2)}%
            </div>
            <div className={`text-xs ${colorClass}`}>
              {isPositive ? '+' : ''}${movement.change.toFixed(2)}
            </div>
          </div>
        </div>
        <div className="flex justify-between items-center pt-1">
          <span className="text-xs text-[var(--foreground-secondary)]">Volume</span>
          <span className="text-xs text-[var(--foreground-secondary)]">
            {(movement.volume / 1000000).toFixed(1)}M
          </span>
        </div>
      </div>
    </div>
  );
}
