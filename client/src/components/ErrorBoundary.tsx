import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary 捕獲到錯誤:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-6 border border-red-300 bg-red-50 rounded-lg">
            <h2 className="text-xl font-bold text-red-700 mb-4">組件發生錯誤</h2>
            <details className="mb-4">
              <summary className="font-semibold text-red-600">錯誤詳情:</summary>
              <pre className="mt-2 text-sm text-red-800 bg-red-100 p-2 rounded overflow-auto">
                {this.state.error && this.state.error.toString()}
              </pre>
            </details>
            {this.state.errorInfo && (
              <details>
                <summary className="font-semibold text-red-600">堆疊跟蹤:</summary>
                <pre className="mt-2 text-sm text-red-800 bg-red-100 p-2 rounded overflow-auto">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            <button 
              onClick={() => this.setState({ hasError: false, error: undefined, errorInfo: undefined })}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              重試
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
