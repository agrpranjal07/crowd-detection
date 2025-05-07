import React from 'react';

export class ErrorBoundary extends React.Component {
    state = { hasError: false };

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Error boundary caught:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-fallback">
                    <h2>Something went wrong with the visualization</h2>
                    <button onClick={() => window.location.reload()}>
                        Reload Application
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}