import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AuthModal from '../components/AuthModal';

beforeEach(() => {
  window.localStorage.removeItem('clauseflag_token');
  window.localStorage.removeItem('clauseflag_user');
});

describe('AuthModal', () => {
  const defaults = {
    open: true,
    onOpenChange: vi.fn(),
    onSuccess: vi.fn(),
  };

  it('renders login heading when open', () => {
    render(<AuthModal {...defaults} />);
    expect(
      screen.getByRole('heading', { name: 'Log in' }),
    ).toBeInTheDocument();
  });

  it('shows username and password fields', () => {
    render(<AuthModal {...defaults} />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('shows login/register toggle buttons', () => {
    render(<AuthModal {...defaults} />);
    const buttons = screen.getAllByRole('button', { name: /Log in|Register/ });
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });

  it('switches heading to Create account when Register tab is clicked', async () => {
    const user = userEvent.setup();
    render(<AuthModal {...defaults} />);

    const registerButtons = screen.getAllByRole('button', {
      name: 'Register',
    });
    await user.click(registerButtons[0]);

    expect(
      screen.getByRole('heading', { name: 'Create account' }),
    ).toBeInTheDocument();
  });

  it('does not render content when closed', () => {
    render(<AuthModal {...defaults} open={false} />);
    expect(screen.queryByLabelText('Username')).not.toBeInTheDocument();
  });

  it('has a close button with accessible label', () => {
    render(<AuthModal {...defaults} />);
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
  });

  it('shows description text for login mode', () => {
    render(<AuthModal {...defaults} />);
    expect(
      screen.getByText('Sign in to save your analysis history.'),
    ).toBeInTheDocument();
  });
});
