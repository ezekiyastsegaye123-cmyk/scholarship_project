import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthModal } from '../components/AuthModal';
import * as client from '../api/client';
import type { StudentAccount } from '../types';

vi.mock('../api/client');

describe('AuthModal Component', () => {
  const mockAccount: StudentAccount = {
    id: 'test-acc-123',
    email: 'test@example.edu',
    is_active: true,
    has_profile: false,
    created_at: '2026-09-11T12:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sign in modal with required accessible attributes and fields', () => {
    render(
      <AuthModal
        isOpen={true}
        initialMode="login"
        onClose={vi.fn()}
        onAuthSuccess={vi.fn()}
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/Sign In to Student Account/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Student Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByText(/Passwords are salted and cryptographically hashed with scrypt/i)).toBeInTheDocument();
  });

  it('switches to create account mode with confirm password field', () => {
    render(
      <AuthModal
        isOpen={true}
        initialMode="login"
        onClose={vi.fn()}
        onAuthSuccess={vi.fn()}
      />
    );

    const createTab = screen.getByRole('button', { name: /Create Account/i });
    fireEvent.click(createTab);

    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
  });

  it('displays client-side validation error when password is shorter than 8 chars', async () => {
    render(
      <AuthModal
        isOpen={true}
        initialMode="login"
        onClose={vi.fn()}
        onAuthSuccess={vi.fn()}
      />
    );

    const emailInput = screen.getByLabelText(/Student Email Address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitBtn = screen.getByTestId('auth-submit-btn');

    fireEvent.change(emailInput, { target: { value: 'short@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'short' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Password must be at least 8 characters long/i);
    });
  });

  it('successfully logs in and calls onAuthSuccess', async () => {
    const onAuthSuccess = vi.fn();
    const onClose = vi.fn();
    vi.spyOn(client, 'authLogin').mockResolvedValue({
      token: 'mock-jwt-token',
      token_type: 'bearer',
      expires_at: '2026-09-12T12:00:00Z',
      account: mockAccount,
    });

    render(
      <AuthModal
        isOpen={true}
        initialMode="login"
        onClose={onClose}
        onAuthSuccess={onAuthSuccess}
      />
    );

    const emailInput = screen.getByLabelText(/Student Email Address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitBtn = screen.getByTestId('auth-submit-btn');

    fireEvent.change(emailInput, { target: { value: 'test@example.edu' } });
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(client.authLogin).toHaveBeenCalledWith('test@example.edu', 'ValidPassword123!');
      expect(onAuthSuccess).toHaveBeenCalledWith(mockAccount);
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('displays server error message on login failure', async () => {
    vi.spyOn(client, 'authLogin').mockRejectedValue(
      new Error('Invalid credentials provided.')
    );

    render(
      <AuthModal
        isOpen={true}
        initialMode="login"
        onClose={vi.fn()}
        onAuthSuccess={vi.fn()}
      />
    );

    const emailInput = screen.getByLabelText(/Student Email Address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitBtn = screen.getByTestId('auth-submit-btn');

    fireEvent.change(emailInput, { target: { value: 'test@example.edu' } });
    fireEvent.change(passwordInput, { target: { value: 'WrongPassword123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Invalid credentials provided/i);
    });
  });
});
