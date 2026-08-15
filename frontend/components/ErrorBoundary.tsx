"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertOctagon, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
  panelName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`ErrorBoundary caught in [${this.props.panelName || "Panel"}]:`, error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-6 rounded-lg border border-[#222730] bg-[#14171C] text-center space-y-3 min-h-[220px]">
          <div className="p-2.5 rounded-lg bg-[#E85D4E]/10 border border-[#E85D4E]/30 text-[#E85D4E]">
            <AlertOctagon className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#E8EAED] font-mono">
              {this.props.panelName || "Component"} Telemetry Fault
            </h4>
            <p className="text-[11px] text-[#8B92A0] max-w-sm mt-1 font-mono">
              {this.state.error?.message || "An unexpected data parsing exception occurred."}
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono font-medium border border-[#222730] bg-[#191D24] text-[#E8EAED] hover:border-[#4A9EFF] transition-colors"
          >
            <RotateCcw className="h-3 w-3 text-[#4A9EFF]" />
            Retry Panel Telemetry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
