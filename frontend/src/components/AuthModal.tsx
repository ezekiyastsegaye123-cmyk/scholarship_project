import React, { useState, useEffect } from 'react';
import { X, Lock, Mail, Loader2, AlertCircle, ShieldCheck } from 'lucide-react';
import { authLogin, authRegister } from '../api/client';
import type { StudentAccount } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  initialMode?: 'login' | 'register';
  onClose: () => void;
  onAuthSuccess: (account: StudentAccount) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  initialMode = 'login',
  onClose,
  onAuthSuccess,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setMode(initialMode);
    setErrorMessage(null);
  }, [initialMode, isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setErrorMessage('Email address is required.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    if (mode === 'register' && password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please verify.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'login') {
        const res = await authLogin(cleanEmail, password);
        onAuthSuccess(res.account);
        onClose();
      } else {
        const res = await authRegister(cleanEmail, password);
        onAuthSuccess(res.account);
        onClose();
      }
    } catch (err: any) {
      const msg = (err && (err.message || err.detail)) || 'Authentication request failed. Please try again.';
      setErrorMessage(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-dialog auth-modal">
        <div className="modal-header">
          <div className="flex items-center gap-2">
            <div className="modal-icon-badge">
              <ShieldCheck className="w-5 h-5 text-brand" />
            </div>
            <h2 id="auth-modal-title" className="modal-title">
              {mode === 'login' ? 'Sign In to Student Account' : 'Create Student Account'}
            </h2>
          </div>
          <button
            type="button"
            className="btn-close-modal"
            onClick={onClose}
            aria-label="Close authentication modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="auth-tab-switch">
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => {
              setMode('login');
              setErrorMessage(null);
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => {
              setMode('register');
              setErrorMessage(null);
            }}
          >
            Create Account
          </button>
        </div>

        {errorMessage && (
          <div className="auth-error-banner" role="alert">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="auth-email">Student Email Address</label>
            <div className="input-with-icon">
              <Mail className="w-4 h-4 text-gray-400 input-icon" />
              <input
                id="auth-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@example.edu"
                className="form-input with-left-icon"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="auth-password">Password (minimum 8 characters)</label>
            <div className="input-with-icon">
              <Lock className="w-4 h-4 text-gray-400 input-icon" />
              <input
                id="auth-password"
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="form-input with-left-icon"
                disabled={loading}
              />
            </div>
          </div>

          {mode === 'register' && (
            <div className="form-group">
              <label htmlFor="auth-confirm-password">Confirm Password</label>
              <div className="input-with-icon">
                <Lock className="w-4 h-4 text-gray-400 input-icon" />
                <input
                  id="auth-confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="form-input with-left-icon"
                  disabled={loading}
                />
              </div>
            </div>
          )}

          <div className="auth-guarantee-note">
            <ShieldCheck className="w-4 h-4 text-brand flex-shrink-0" />
            <span>
              Passwords are salted and cryptographically hashed with scrypt ($N=16384$). No tracking scripts, advertising pixels, or data sales.
            </span>
          </div>

          <button
            type="submit"
            className="btn-primary w-full justify-center mt-4"
            disabled={loading}
            data-testid="auth-submit-btn"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {mode === 'login' ? 'Signing In...' : 'Creating Account...'}
              </>
            ) : mode === 'login' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
