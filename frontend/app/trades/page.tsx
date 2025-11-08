'use client';

import { useState } from 'react';
import { apiClient, TradeRequest, TradeResponse } from '@/lib/api-client';
import Link from 'next/link';

export default function TradesPage() {
  const [formData, setFormData] = useState<TradeRequest>({
    ticker: '',
    action: 'BUY',
    s_final: 0.5,
    quantity: undefined,
    reason: '',
  });
  const [response, setResponse] = useState<TradeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await apiClient.executeTrade(formData);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trade execution failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-8">
      {/* Animated background */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 -right-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 md:mb-12 fade-in-up">
          <Link href="/" className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 mb-6 transition-colors group">
            <span className="group-hover:-translate-x-1 transition-transform">←</span>
            Back to Dashboard
          </Link>
          <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-2">Execute Trade</h1>
          <p className="text-[var(--foreground-secondary)] text-lg">Enter your trade parameters below</p>
        </div>

        <div className="glass-card rounded-2xl p-6 md:p-10">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Ticker Input */}
            <div>
              <label className="block text-sm font-semibold mb-3 text-[var(--foreground)]">
                Ticker Symbol
              </label>
              <input
                type="text"
                value={formData.ticker}
                onChange={(e: any) => setFormData({ ...formData, ticker: e.target.value.toUpperCase() })}
                className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all text-lg font-bold uppercase placeholder:normal-case placeholder:font-normal"
                placeholder="e.g., AAPL"
                required
              />
            </div>

            {/* Action Buttons */}
            <div>
              <label className="block text-sm font-semibold mb-3 text-[var(--foreground)]">
                Action
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, action: 'BUY' })}
                  className={`relative py-5 rounded-xl font-bold text-lg transition-all ${
                    formData.action === 'BUY'
                      ? 'bg-green-500 text-white shadow-lg shadow-green-500/30 scale-105'
                      : 'bg-[var(--background-secondary)] text-[var(--foreground-secondary)] border-2 border-[var(--border-color)] hover:border-green-500/50 hover:text-green-400'
                  }`}
                >
                  {formData.action === 'BUY' && <div className="absolute inset-0 bg-green-400 rounded-xl blur-xl opacity-20"></div>}
                  <span className="relative">📈 BUY</span>
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, action: 'SELL' })}
                  className={`relative py-5 rounded-xl font-bold text-lg transition-all ${
                    formData.action === 'SELL'
                      ? 'bg-red-500 text-white shadow-lg shadow-red-500/30 scale-105'
                      : 'bg-[var(--background-secondary)] text-[var(--foreground-secondary)] border-2 border-[var(--border-color)] hover:border-red-500/50 hover:text-red-400'
                  }`}
                >
                  {formData.action === 'SELL' && <div className="absolute inset-0 bg-red-400 rounded-xl blur-xl opacity-20"></div>}
                  <span className="relative">📉 SELL</span>
                </button>
              </div>
            </div>

            {/* Investment Score Slider */}
            <div>
              <label className="block text-sm font-semibold mb-3 text-[var(--foreground)]">
                Investment Score (Conviction Level)
              </label>
              <div className="space-y-4">
                <div className="flex items-center justify-between px-1">
                  <span className="text-2xl font-bold text-white">{formData.s_final.toFixed(2)}</span>
                  <span className="text-sm text-[var(--foreground-secondary)]">
                    {formData.s_final < 0.3 ? 'Low' : formData.s_final < 0.7 ? 'Medium' : 'High'} Conviction
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={formData.s_final}
                  onChange={(e: any) => setFormData({ ...formData, s_final: parseFloat(e.target.value) })}
                  className="w-full h-3 bg-[var(--background-secondary)] rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-gradient-to-r [&::-webkit-slider-thumb]:from-blue-500 [&::-webkit-slider-thumb]:to-purple-500 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-blue-500/50"
                  style={{
                    background: `linear-gradient(to right, rgb(59, 130, 246) ${formData.s_final * 100}%, var(--background-secondary) ${formData.s_final * 100}%)`
                  }}
                />
                <p className="text-xs text-[var(--foreground-secondary)] px-1">
                  Higher score increases position sizing based on conviction
                </p>
              </div>
            </div>

            {/* Quantity Input */}
            <div>
              <label className="block text-sm font-semibold mb-3 text-[var(--foreground)]">
                Quantity <span className="text-[var(--foreground-secondary)] font-normal">(Optional)</span>
              </label>
              <input
                type="number"
                value={formData.quantity || ''}
                onChange={(e: any) =>
                  setFormData({ ...formData, quantity: e.target.value ? parseFloat(e.target.value) : undefined })
                }
                className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-purple-500 focus:ring-4 focus:ring-purple-500/20 transition-all text-lg"
                placeholder="Auto-calculated"
                step="0.01"
                min="0"
              />
              <p className="text-xs text-[var(--foreground-secondary)] mt-2 px-1">
                Leave blank for automatic position sizing based on conviction score
              </p>
            </div>

            {/* Reason Input */}
            <div>
              <label className="block text-sm font-semibold mb-3 text-[var(--foreground)]">
                Trade Reason
              </label>
              <input
                type="text"
                value={formData.reason}
                onChange={(e: any) => setFormData({ ...formData, reason: e.target.value })}
                className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all text-lg"
                placeholder="e.g., Strong earnings beat, AI momentum"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-5 bg-white text-black rounded-xl font-bold text-lg hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="flex items-center justify-center gap-2">
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-3 border-black border-t-transparent rounded-full animate-spin"></div>
                    Executing Trade...
                  </>
                ) : (
                  <>
                    ⚡ Execute {formData.action} Order
                  </>
                )}
              </span>
            </button>
          </form>

          {/* Error Message */}
          {error && (
            <div className="mt-8 p-6 bg-red-500/10 border-2 border-red-500/50 rounded-xl backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <div className="text-2xl">⚠️</div>
                <div className="flex-1">
                  <p className="text-red-400 font-bold text-lg mb-1">Trade Failed</p>
                  <p className="text-red-300">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Success/Response Message */}
          {response && (
            <div
              className={`mt-8 p-6 rounded-xl backdrop-blur-sm border-2 ${
                response.success
                  ? 'bg-green-500/10 border-green-500/50'
                  : 'bg-red-500/10 border-red-500/50'
              }`}
            >
              <div className="flex items-start gap-3 mb-4">
                <div className="text-3xl">{response.success ? '✅' : '❌'}</div>
                <div>
                  <p className={`font-bold text-xl ${response.success ? 'text-green-400' : 'text-red-400'}`}>
                    {response.success ? 'Trade Executed Successfully!' : 'Trade Execution Failed'}
                  </p>
                  <p className="text-[var(--foreground-secondary)] mt-1">{response.message}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-[var(--border-color)]">
                <div>
                  <p className="text-xs text-[var(--foreground-secondary)] mb-1">Order ID</p>
                  <p className="font-mono font-semibold">{response.order_id || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--foreground-secondary)] mb-1">Ticker</p>
                  <p className="font-bold text-lg">{response.ticker}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--foreground-secondary)] mb-1">Action</p>
                  <p className={`font-bold ${response.action === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                    {response.action}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--foreground-secondary)] mb-1">Quantity</p>
                  <p className="font-semibold">{response.quantity}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--foreground-secondary)] mb-1">Price</p>
                  <p className="font-mono font-semibold">${response.price?.toFixed(2) || 'N/A'}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
