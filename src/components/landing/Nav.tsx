import { useState } from "react";

const API_BASE =
  typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8001"
    : "";

export function Nav() {
  const [showLoginModal, setShowLoginModal] = useState(false);

  const handleGoogleLogin = () => {
    window.location.href = `${API_BASE}/auth/google`;
  };

  const handleDemoLogin = () => {
    window.location.href = `${API_BASE}/auth/demo`;
  };

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-[var(--line-strong)] bg-[color-mix(in_oklab,var(--ghost)_85%,transparent)] backdrop-blur">
        <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-3 font-display text-lg tracking-tight">
            <img src="/logo.png" alt="StandupBot" className="w-8 h-8 object-contain" />
            <span className="font-bold">StandupBot</span>
          </a>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[var(--ink-soft)]">
            <a href="#how" className="hover:text-[var(--ink)]">How it works</a>
            <a href="#features" className="hover:text-[var(--ink)]">Features</a>
            <a href="#problem" className="hover:text-[var(--ink)]">Why us</a>
            <a href="#cta" className="hover:text-[var(--ink)]">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowLoginModal(true)}
              className="btn-primary text-sm !py-2 !px-4 rounded-full"
            >
              Start free
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      {showLoginModal && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm"
          onClick={() => setShowLoginModal(false)}
        >
          <div
            className="relative bg-[var(--surface)] border-2 border-[var(--line-strong)] w-full max-w-md mx-4 p-8 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-[var(--ink-soft)] hover:text-[var(--ink)]"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>

            {/* Modal content */}
            <div className="text-center mb-8">
              <img src="/logo.png" alt="StandupBot" className="w-16 h-16 mx-auto mb-4 object-contain" />
              <h2 className="font-display text-2xl font-bold text-[var(--ink)]">Welcome to StandupBot</h2>
              <p className="text-sm text-[var(--ink-soft)] mt-2">Sign in to start your first project</p>
            </div>

            {/* Google Sign In Button */}
            <button
              onClick={handleGoogleLogin}
              className="w-full flex items-center justify-center gap-3 px-6 py-4 border-2 border-[var(--line-strong)] bg-[var(--surface)] hover:bg-[var(--surface-2)] transition-colors mb-3"
            >
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span className="font-semibold text-[var(--ink)]">Continue with Google</span>
            </button>

            {/* Demo Login Button */}
            <button
              onClick={handleDemoLogin}
              className="w-full flex items-center justify-center gap-3 px-6 py-4 border-2 border-[var(--persian)] bg-[var(--persian)] hover:opacity-90 transition-opacity text-white mb-6"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13 12H3"/></svg>
              <span className="font-semibold">Try Demo — no sign in needed</span>
            </button>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[var(--line)]"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-[var(--surface)] px-2 text-[var(--ink-soft)]">or</span>
              </div>
            </div>

            {/* Email/Password fields (disabled for now) */}
            <div className="space-y-4 opacity-50 pointer-events-none">
              <div>
                <label className="block text-xs font-semibold text-[var(--ink)] mb-2 uppercase tracking-wider">
                  Email
                </label>
                <input
                  type="email"
                  disabled
                  className="w-full px-4 py-3 border border-[var(--line-strong)] bg-[var(--surface-2)] text-[var(--ink)]"
                  placeholder="your@email.com"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--ink)] mb-2 uppercase tracking-wider">
                  Password
                </label>
                <input
                  type="password"
                  disabled
                  className="w-full px-4 py-3 border border-[var(--line-strong)] bg-[var(--surface-2)] text-[var(--ink)]"
                  placeholder="••••••••"
                />
              </div>
              <button
                disabled
                className="w-full py-3 bg-[var(--ink)] text-[var(--ghost)] font-semibold"
              >
                Log in
              </button>
            </div>

            <div className="mt-6 text-center space-y-2">
              <a href="#" className="block text-sm text-[var(--persian)] hover:underline">
                Use single sign-on
              </a>
              <a href="#" className="block text-sm text-[var(--persian)] hover:underline">
                Reset password
              </a>
              <p className="text-sm text-[var(--ink-soft)]">
                No account?{" "}
                <a href="#" className="text-[var(--persian)] hover:underline">
                  Create one
                </a>
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
