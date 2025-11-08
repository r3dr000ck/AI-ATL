'use client';

import { useEffect, useState } from 'react';
import { apiClient, HealthStatus, PositionsResponse } from '@/lib/api-client';
import Link from 'next/link';

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [positions, setPositions] = useState<PositionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-red-500 text-xl">Error: {error}</div>
      </div>
    );
  }

  const totalPnL = positions?.positions.reduce((sum, p) => sum + (p.pnl || 0), 0) || 0;

  return (
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
          </div>

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
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCard({ title, value, color }: { title: string; value: string; color: string }) {
  const colorClasses: Record<string, string> = {
    green: 'bg-green-900/50 text-green-400 border-green-700',
    red: 'bg-red-900/50 text-red-400 border-red-700',
    blue: 'bg-blue-900/50 text-blue-400 border-blue-700',
    purple: 'bg-purple-900/50 text-purple-400 border-purple-700',
  };

  return (
    <div className={`bg-gray-800 rounded-lg border-2 ${colorClasses[color]} p-6`}>
      <h3 className="text-gray-400 text-sm font-medium mb-2">{title}</h3>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}
