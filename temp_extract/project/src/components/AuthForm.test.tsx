import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { AuthForm } from './AuthForm';
import { supabase } from '../services/api';

vi.mock('../services/api', () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
    },
  },
}));

describe('AuthForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnToggleMode = vi.fn();
  const mockOnForgotPassword = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('validates email format', async () => {
    render(
      <AuthForm
        mode="signin"
        onSubmit={mockOnSubmit}
        onToggleMode={mockOnToggleMode}
        onForgotPassword={mockOnForgotPassword}
      />
    );

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'invalid-email' },
    });

    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('validates password requirements', async () => {
    render(
      <AuthForm
        mode="signup"
        onSubmit={mockOnSubmit}
        onToggleMode={mockOnToggleMode}
        onForgotPassword={mockOnForgotPassword}
      />
    );

    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'weak' },
    });

    fireEvent.submit(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('handles successful sign in', async () => {
    vi.mocked(supabase.auth.signInWithPassword).mockResolvedValueOnce({
      data: { user: { id: '123' }, session: {} },
      error: null,
    });

    render(
      <AuthForm
        mode="signin"
        onSubmit={mockOnSubmit}
        onToggleMode={mockOnToggleMode}
        onForgotPassword={mockOnForgotPassword}
      />
    );

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'Password123' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'Password123',
        rememberMe: false,
      });
    });
  });
});