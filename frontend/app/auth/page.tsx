'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function AuthPage() {
  const { login, signup } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [signupData, setSignupData] = useState({ email: '', password: '', confirmPassword: '', name: '' });
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(loginData.email, loginData.password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (signupData.password !== signupData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (signupData.password.length < 8) {
      setError('Password must be at least 8 characters');
      setLoading(false);
      return;
    }

    try {
      await signup(signupData.email, signupData.password, signupData.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden relative">
      {/* Geometric Grid Background */}
      <div className="fixed inset-0 -z-10 geometric-grid"></div>

      {/* Triangle geometric elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Top left */}
        <div className="triangle-pattern triangle-down triangle-animate absolute top-20 left-10" style={{ borderWidth: '0 80px 140px 80px' }}></div>
        <div className="triangle-pattern triangle-right triangle-animate-slow absolute top-40 left-40" style={{ borderWidth: '60px 0 60px 104px' }}></div>

        {/* Top right */}
        <div className="triangle-pattern triangle-up triangle-animate-slow absolute top-32 right-20" style={{ borderWidth: '0 70px 121px 70px' }}></div>

        {/* Middle */}
        <div className="triangle-pattern triangle-left triangle-animate absolute top-1/2 left-1/4" style={{ borderWidth: '50px 87px 50px 0', opacity: '0.5' }}></div>
        <div className="triangle-pattern triangle-down triangle-animate-slow absolute top-1/3 right-1/4" style={{ borderWidth: '100px 58px 0 58px' }}></div>

        {/* Bottom */}
        <div className="triangle-pattern triangle-up triangle-animate absolute bottom-40 left-1/3" style={{ borderWidth: '0 90px 156px 90px' }}></div>
        <div className="triangle-pattern triangle-right triangle-animate-slow absolute bottom-20 right-40" style={{ borderWidth: '70px 0 70px 121px' }}></div>
      </div>

      {/* Navigation Bar */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrollY > 50 ? 'glass-card border-b border-[var(--border-color)]' : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold text-white tracking-tight">
            ValueCell AI
          </Link>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowLoginModal(true)}
              className="px-6 py-2.5 text-white hover:text-gray-300 font-medium"
            >
              Log In
            </button>
            <button
              onClick={() => setShowSignupModal(true)}
              className="px-6 py-2.5 bg-white text-black rounded-full font-semibold hover:bg-gray-200 hover:scale-105"
            >
              Sign Up
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center px-6 pt-20 relative">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-7xl md:text-8xl font-bold text-white mb-8 leading-tight tracking-tight opacity-0 animate-[fade-in-scale_0.8s_ease-out_forwards]">
            The Future of<br/>Trading is Here
          </h1>
          <p className="text-2xl md:text-3xl text-gray-400 mb-12 font-light opacity-0 animate-[fade-in-scale_0.8s_ease-out_0.2s_forwards]">
            Powered by cutting-edge <span className="text-white font-medium">Large Language Models</span>
          </p>
          <div className="flex items-center justify-center gap-3 mb-8 opacity-0 animate-[fade-in-scale_0.8s_ease-out_0.4s_forwards]">
            <div className="w-24 h-px bg-gradient-to-r from-transparent via-white to-transparent"></div>
            <div className="w-2 h-2 bg-white rounded-full"></div>
            <div className="w-24 h-px bg-gradient-to-r from-transparent via-white to-transparent"></div>
          </div>
        </div>
      </section>

      {/* Vision Section */}
      <section className="min-h-screen flex items-center justify-center px-6 py-20 relative">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-16 text-center tracking-tight">
            Why LLM Trading?
          </h2>
          <div className="space-y-8 text-xl md:text-2xl text-gray-400 leading-relaxed font-light">
            <p>
              Traditional algorithmic trading relies on <span className="text-gray-300">rigid rules</span> and predefined strategies.
              But the market is <span className="text-white font-normal">dynamic, complex, and constantly evolving</span>.
            </p>
            <p>
              Large Language Models bring <span className="text-white font-normal">unprecedented adaptability</span> to trading.
              They can analyze news sentiment, understand market context, and make nuanced decisions that go beyond
              simple technical indicators.
            </p>
            <p className="text-white font-normal text-2xl md:text-3xl mt-12">
              ValueCell AI Trader harnesses this power to give you an edge in the market.
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="min-h-screen flex items-center justify-center px-6 py-20 relative">
        <div className="max-w-7xl mx-auto w-full">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-20 text-center tracking-tight">
            Built for the Future
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="glass-card p-10 rounded-3xl hover-glow group relative overflow-hidden">
              {/* Small triangle accent */}
              <div className="triangle-pattern triangle-up absolute top-4 right-4 opacity-20" style={{ borderWidth: '0 15px 26px 15px', borderColor: 'transparent transparent white transparent' }}></div>

              <div className="text-5xl mb-6 group-hover:scale-110 transition-transform duration-300">🧠</div>
              <h3 className="text-3xl font-bold text-white mb-4 tracking-tight">AI-Powered Decisions</h3>
              <p className="text-gray-400 text-lg leading-relaxed">
                Our LLM analyzes market sentiment, news, and technical data to make informed trading decisions.
              </p>
            </div>
            <div className="glass-card p-10 rounded-3xl hover-glow group relative overflow-hidden">
              {/* Small triangle accent */}
              <div className="triangle-pattern triangle-down absolute top-4 right-4 opacity-20" style={{ borderWidth: '26px 15px 0 15px', borderColor: 'white transparent transparent transparent' }}></div>

              <div className="text-5xl mb-6 group-hover:scale-110 transition-transform duration-300">⚡</div>
              <h3 className="text-3xl font-bold text-white mb-4 tracking-tight">Real-Time Execution</h3>
              <p className="text-gray-400 text-lg leading-relaxed">
                Execute trades instantly with our optimized infrastructure and automated position management.
              </p>
            </div>
            <div className="glass-card p-10 rounded-3xl hover-glow group relative overflow-hidden">
              {/* Small triangle accent */}
              <div className="triangle-pattern triangle-right absolute top-4 right-4 opacity-20" style={{ borderWidth: '15px 0 15px 26px', borderColor: 'transparent transparent transparent white' }}></div>

              <div className="text-5xl mb-6 group-hover:scale-110 transition-transform duration-300">📊</div>
              <h3 className="text-3xl font-bold text-white mb-4 tracking-tight">Advanced Analytics</h3>
              <p className="text-gray-400 text-lg leading-relaxed">
                Track performance, analyze positions, and optimize your strategy with detailed insights.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="min-h-screen flex items-center justify-center px-6 py-20 relative">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-6xl md:text-7xl font-bold text-white mb-8 tracking-tight leading-tight">
            Join The<br/>Movement Now
          </h2>
          <p className="text-2xl text-gray-400 mb-16 font-light">
            Be part of the next generation of algorithmic traders
          </p>
          <button
            onClick={() => setShowSignupModal(true)}
            className="group relative px-14 py-6 bg-white text-black rounded-full text-xl font-bold hover:bg-gray-200 hover:scale-105"
          >
            <span className="relative z-10">Get Started Today</span>
          </button>

          {/* Social Proof / Stats */}
          <div className="mt-20 grid grid-cols-3 gap-8 max-w-3xl mx-auto">
            <div className="text-center relative">
              <div className="triangle-pattern triangle-up mx-auto mb-4" style={{ borderWidth: '0 10px 17px 10px', borderColor: 'transparent transparent rgba(255,255,255,0.2) transparent' }}></div>
              <div className="text-4xl font-bold text-white mb-2">99.9%</div>
              <div className="text-sm text-gray-400 uppercase tracking-wider">Uptime</div>
            </div>
            <div className="text-center relative">
              <div className="triangle-pattern triangle-down mx-auto mb-4" style={{ borderWidth: '17px 10px 0 10px', borderColor: 'rgba(255,255,255,0.2) transparent transparent transparent' }}></div>
              <div className="text-4xl font-bold text-white mb-2">&lt;10ms</div>
              <div className="text-sm text-gray-400 uppercase tracking-wider">Latency</div>
            </div>
            <div className="text-center relative">
              <div className="triangle-pattern triangle-up mx-auto mb-4" style={{ borderWidth: '0 10px 17px 10px', borderColor: 'transparent transparent rgba(255,255,255,0.2) transparent' }}></div>
              <div className="text-4xl font-bold text-white mb-2">24/7</div>
              <div className="text-sm text-gray-400 uppercase tracking-wider">Trading</div>
            </div>
          </div>
        </div>
      </section>

      {/* Login Modal */}
      {showLoginModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
          onClick={() => {
            setShowLoginModal(false);
            setError(null);
          }}
        >
          <div
            className="glass-card rounded-3xl p-10 max-w-md w-full relative opacity-0 animate-[fade-in-scale_0.3s_ease-out_forwards]"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => {
                setShowLoginModal(false);
                setError(null);
              }}
              className="absolute top-6 right-6 text-3xl text-gray-400 hover:text-white"
            >
              ×
            </button>
            <h2 className="text-4xl font-bold text-white mb-8 tracking-tight">Welcome Back</h2>
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold mb-3 text-white">Email</label>
                <input
                  type="email"
                  value={loginData.email}
                  onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                  className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-white text-white placeholder:text-gray-500"
                  placeholder="you@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-3 text-white">Password</label>
                <input
                  type="password"
                  value={loginData.password}
                  onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                  className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-white text-white placeholder:text-gray-500"
                  placeholder="••••••••"
                  required
                />
              </div>
              {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400 text-sm">
                  {error}
                </div>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-white text-black rounded-xl font-bold text-lg hover:bg-gray-200 disabled:opacity-50 mt-6"
              >
                {loading ? 'Logging in...' : 'Log In'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Signup Modal */}
      {showSignupModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
          onClick={() => {
            setShowSignupModal(false);
            setError(null);
          }}
        >
          <div
            className="glass-card rounded-3xl p-10 max-w-md w-full relative opacity-0 animate-[fade-in-scale_0.3s_ease-out_forwards]"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => {
                setShowSignupModal(false);
                setError(null);
              }}
              className="absolute top-6 right-6 text-3xl text-gray-400 hover:text-white"
            >
              ×
            </button>
            <h2 className="text-4xl font-bold text-white mb-8 tracking-tight">Get Started</h2>
            <form onSubmit={handleSignup} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold mb-3 text-white">Name</label>
                <input
                  type="text"
                  value={signupData.name}
                  onChange={(e) => setSignupData({ ...signupData, name: e.target.value })}
                  className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-white text-white placeholder:text-gray-500"
                  placeholder="John Doe"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-3 text-white">Email</label>
                <input
                  type="email"
                  value={signupData.email}
                  onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                  className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-white text-white placeholder:text-gray-500"
                  placeholder="you@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-3 text-white">Password</label>
                <input
                  type="password"
                  value={signupData.password}
                  onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                  className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-white text-white placeholder:text-gray-500"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-3 text-white">Confirm Password</label>
                <input
                  type="password"
                  value={signupData.confirmPassword}
                  onChange={(e) => setSignupData({ ...signupData, confirmPassword: e.target.value })}
                  className="w-full px-5 py-4 bg-[var(--background-secondary)] border-2 border-[var(--border-color)] rounded-xl focus:outline-none focus:border-white text-white placeholder:text-gray-500"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>
              {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400 text-sm">
                  {error}
                </div>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-white text-black rounded-xl font-bold text-lg hover:bg-gray-200 disabled:opacity-50 mt-6"
              >
                {loading ? 'Creating account...' : 'Create Account'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
