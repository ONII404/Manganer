import React from "react";
import { cn } from "@/lib/utils";
import { Database, Activity, Settings, BookOpen } from "lucide-react";

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function Layout({ children, activeTab, onTabChange }: LayoutProps) {
  const tabs = [
    { id: "library", label: "Biblioteca", icon: BookOpen },
    { id: "tasks", label: "Tareas", icon: Activity },
    { id: "metrics", label: "Métricas", icon: Database },
    { id: "settings", label: "Configuración", icon: Settings },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-lg font-semibold">Manganer</h1>
            <span className="text-xs text-textMuted px-2 py-0.5 rounded-full bg-surfaceHighlight">
              v0.1.0
            </span>
          </div>

          {/* Tabs */}
          <nav className="flex items-center gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors",
                  activeTab === tab.id
                    ? "bg-primary text-white"
                    : "text-textMuted hover:text-text hover:bg-surfaceHighlight",
                )}
              >
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-3 text-center text-xs text-textMuted">
        Manganer • Python 3.13 • FastAPI • React 18
      </footer>
    </div>
  );
}
