import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

beforeEach(() => {
  window.localStorage.removeItem('clauseflag_token');
  window.localStorage.removeItem('clauseflag_user');
});

describe('App', () => {
  it('renders the ClauseFlag heading', () => {
    render(<App />);
    expect(
      screen.getByRole('heading', { name: 'ClauseFlag' }),
    ).toBeInTheDocument();
  });

  it('shows Log in button when not authenticated', () => {
    render(<App />);
    expect(screen.getByText('Log in')).toBeInTheDocument();
  });

  it('shows the text/url mode toggle', () => {
    render(<App />);
    expect(screen.getByText('Paste Text')).toBeInTheDocument();
    expect(screen.getByText('URL')).toBeInTheDocument();
  });

  it('shows the Analyze clauses button', () => {
    render(<App />);
    expect(
      screen.getByRole('button', { name: 'Analyze clauses' }),
    ).toBeInTheDocument();
  });

  it('shows empty results placeholder initially', () => {
    render(<App />);
    expect(screen.getByText(/No analysis yet/)).toBeInTheDocument();
  });

  it('switches between text and url input modes', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: 'URL' }));
    expect(screen.getByPlaceholderText(/example\.com/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Paste Text' }));
    expect(
      screen.getByPlaceholderText(/Paste the full text/),
    ).toBeInTheDocument();
  });

  it('shows username and logout when user is stored', () => {
    window.localStorage.setItem('clauseflag_token', 'fake-token');
    window.localStorage.setItem(
      'clauseflag_user',
      JSON.stringify({ user_id: 'u1', username: 'testuser' }),
    );

    render(<App />);
    expect(screen.getByText('testuser')).toBeInTheDocument();
    expect(screen.getByText('Log out')).toBeInTheDocument();
  });

  it('shows My History panel with clickable header when authenticated', () => {
    window.localStorage.setItem('clauseflag_token', 'fake-token');
    window.localStorage.setItem(
      'clauseflag_user',
      JSON.stringify({ user_id: 'u1', username: 'testuser' }),
    );

    render(<App />);
    const historyButton = screen.getByText('My History');
    expect(historyButton).toBeInTheDocument();
    expect(historyButton.closest('button')).not.toBeNull();
  });

  it('does not show history panel when logged out', () => {
    render(<App />);
    expect(screen.queryByText('My History')).not.toBeInTheDocument();
  });

  it('shows risk filter buttons', () => {
    render(<App />);
    for (const label of ['all', 'safe', 'watch', 'danger']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    }
  });
});
