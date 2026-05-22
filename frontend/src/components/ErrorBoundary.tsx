import React from 'react';

interface ErrorBoundaryState {
  error: Error | null;
  info: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallbackLabel?: string;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null, info: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('UI render error:', error, info);
    this.setState({ info });
  }

  reset = () => this.setState({ error: null, info: null });

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div
        style={{
          margin: 20,
          padding: 20,
          border: '1px solid var(--danger)',
          borderRadius: 10,
          background: 'rgba(194, 83, 60, 0.08)',
          color: 'var(--ink)',
          fontFamily: 'inherit',
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>
          {this.props.fallbackLabel || 'Something went wrong rendering this view.'}
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: 'var(--danger)',
            whiteSpace: 'pre-wrap',
            marginBottom: 10,
          }}
        >
          {this.state.error.message}
        </div>
        <button className="btn sm" onClick={this.reset}>
          Try again
        </button>
      </div>
    );
  }
}

export default ErrorBoundary;
