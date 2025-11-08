'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import MiniChart from '@/components/MiniChart';
import PortfolioChart from '@/components/PortfolioChart';
import {
  generatePositions,
  generateAccountSummary,
  generatePortfolioHistory,
  type Position,
  type AccountSummary
} from '@/lib/dummy-data';

const Dither = dynamic(() => import('@/components/Dither'), {
  ssr: false,
  loading: () => null
});

export default function ProfilePage() {
  const { user, logout, isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [timeframe, setTimeframe] = useState<'1D' | '1W' | '1M' | '3M' | '1Y'>('1M');

  // Generate dummy data
  const positions = useMemo(() => generatePositions(), []);
  const accountSummary = useMemo(() => generateAccountSummary(positions), [positions]);

  const portfolioHistory = useMemo(() => {
    const days = {
      '1D': 1,
      '1W': 7,
      '1M': 30,
      '3M': 90,
      '1Y': 365
    }[timeframe];

    const endValue = accountSummary.totalValue;
    const startValue = endValue - accountSummary.totalPnL;

    return generatePortfolioHistory(days, startValue, endValue);
  }, [timeframe, accountSummary]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, authLoading, router]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Dithered Background */}
      <Dither
        waveSpeed={0.015}
        waveFrequency={1.8}
        waveAmplitude={0.3}
        waveColor={[0.1, 0.15, 0.3]}
        colorNum={4}
        pixelSize={3}
        disableAnimation={false}
        enableMouseInteraction={true}
        mouseRadius={1.5}
      />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-[var(--border-color)]">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <h1 className="text-2xl font-bold text-white tracking-tight">Futures AI</h1>
            <div className="flex items-center gap-6">
              <a href="/" className="text-gray-400 hover:text-white transition-colors">
                Dashboard
              </a>
              <a href="/profile" className="text-white font-medium">
                Profile
              </a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-400">{user.email}</span>
            <button
              onClick={() => logout()}
              className="px-4 py-2 text-white hover:text-gray-300 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 pt-32 pb-20 relative z-10">
        {/* Header */}
        <div className="mb-12">
          <h2 className="text-5xl font-bold text-white mb-4 tracking-tight">
            Welcome back, {user.name}
          </h2>
          <p className="text-xl text-gray-400">Here's your trading performance overview</p>
        </div>

        {/* Account Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {/* Total Portfolio Value */}
          <div className="glass-card rounded-2xl p-6">
            <div className="text-sm text-gray-400 mb-2">Total Portfolio Value</div>
            <div className="text-3xl font-bold text-white mb-1">
              ${accountSummary.totalValue.toLocaleString()}
            </div>
            <div className={`text-sm font-medium ${accountSummary.totalPnLPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {accountSummary.totalPnLPercent >= 0 ? '+' : ''}
              {accountSummary.totalPnLPercent.toFixed(2)}%
            </div>
          </div>

          {/* Buying Power */}
          <div className="glass-card rounded-2xl p-6">
            <div className="text-sm text-gray-400 mb-2">Buying Power</div>
            <div className="text-3xl font-bold text-white mb-1">
              ${accountSummary.buyingPower.toLocaleString()}
            </div>
            <div className="text-sm text-gray-400">
              4x Leverage
            </div>
          </div>

          {/* Realized P&L */}
          <div className="glass-card rounded-2xl p-6">
            <div className="text-sm text-gray-400 mb-2">Realized P&L</div>
            <div className={`text-3xl font-bold mb-1 ${accountSummary.realizedPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {accountSummary.realizedPnL >= 0 ? '+' : ''}
              ${accountSummary.realizedPnL.toLocaleString()}
            </div>
            <div className="text-sm text-gray-400">Closed Positions</div>
          </div>

          {/* Unrealized P&L */}
          <div className="glass-card rounded-2xl p-6">
            <div className="text-sm text-gray-400 mb-2">Unrealized P&L</div>
            <div className={`text-3xl font-bold mb-1 ${accountSummary.unrealizedPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {accountSummary.unrealizedPnL >= 0 ? '+' : ''}
              ${accountSummary.unrealizedPnL.toLocaleString()}
            </div>
            <div className="text-sm text-gray-400">Open Positions</div>
          </div>
        </div>

        {/* Portfolio Performance Chart */}
        <div className="glass-card rounded-2xl p-8 mb-12">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">Portfolio Performance</h3>
              <div className={`text-lg font-medium ${accountSummary.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {accountSummary.totalPnL >= 0 ? '+' : ''}
                ${accountSummary.totalPnL.toLocaleString()} ({accountSummary.totalPnLPercent >= 0 ? '+' : ''}
                {accountSummary.totalPnLPercent.toFixed(2)}%)
              </div>
            </div>

            {/* Timeframe Selector */}
            <div className="flex gap-2">
              {(['1D', '1W', '1M', '3M', '1Y'] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    timeframe === tf
                      ? 'bg-white text-black'
                      : 'bg-[var(--background-secondary)] text-gray-400 hover:text-white'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <PortfolioChart data={portfolioHistory} width={900} height={300} />
          </div>
        </div>

        {/* Current Positions */}
        <div className="glass-card rounded-2xl p-8">
          <h3 className="text-2xl font-bold text-white mb-6">Current Positions</h3>

          <div className="space-y-4">
            {positions.map((position) => (
              <div
                key={position.symbol}
                className="bg-[var(--background-secondary)] rounded-xl p-6 hover:bg-[var(--background-secondary)]/80 transition-colors"
              >
                <div className="flex items-center justify-between">
                  {/* Position Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <h4 className="text-xl font-bold text-white">{position.symbol}</h4>
                      <span className="text-sm text-gray-400">{position.name}</span>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-gray-400 mb-1">Quantity</div>
                        <div className="text-white font-medium">{position.quantity}</div>
                      </div>
                      <div>
                        <div className="text-gray-400 mb-1">Avg Price</div>
                        <div className="text-white font-medium">${position.avgPrice.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-gray-400 mb-1">Current Price</div>
                        <div className="text-white font-medium">${position.currentPrice.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-gray-400 mb-1">Market Value</div>
                        <div className="text-white font-medium">${position.marketValue.toLocaleString()}</div>
                      </div>
                    </div>
                  </div>

                  {/* Mini Chart */}
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className={`text-lg font-bold ${position.unrealizedPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {position.unrealizedPnL >= 0 ? '+' : ''}${Math.abs(position.unrealizedPnL).toLocaleString()}
                      </div>
                      <div className={`text-sm font-medium ${position.unrealizedPnLPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {position.unrealizedPnLPercent >= 0 ? '+' : ''}
                        {position.unrealizedPnLPercent.toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-[var(--background)] rounded-lg p-3">
                      <MiniChart
                        data={position.chartData}
                        positive={position.unrealizedPnL >= 0}
                        width={140}
                        height={50}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
