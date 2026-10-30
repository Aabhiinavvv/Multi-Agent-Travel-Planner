import React, { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import {
  Compass,
  Plane,
  Building,
  CloudSun,
  Wallet,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Copy,
  Printer,
  RotateCcw,
  Send,
  Sparkles,
  ArrowRight,
  Bookmark,
  ChevronDown,
  ChevronUp,
  X,
  History,
  ShieldCheck,
  ShieldAlert,
  Download,
  FileText,
  FileCode,
  Check,
} from 'lucide-react';
import { AgentName, SavedTrip, TravelResponse } from './types.js';

const AGENT_META: Record<
  AgentName,
  { label: string; icon: React.ComponentType<{ className?: string }>; color: string }
> = {
  flight_agent: { label: 'Flight Agent', icon: Plane, color: 'text-sky-400 border-sky-500/30 bg-sky-500/10' },
  hotel_agent: { label: 'Hotel Agent', icon: Building, color: 'text-amber-400 border-amber-500/30 bg-amber-500/10' },
  weather_agent: { label: 'Weather Agent', icon: CloudSun, color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' },
  budget_agent: { label: 'Budget Agent', icon: Wallet, color: 'text-purple-400 border-purple-500/30 bg-purple-500/10' },
  itinerary_agent: { label: 'Itinerary Agent', icon: Calendar, color: 'text-teal-400 border-teal-500/30 bg-teal-500/10' },
};

const SUGGESTIONS = [
  'Plan a 5-day trip to Tokyo in April for two people, with great food and a moderate budget.',
  'A relaxing 4-day weekend getaway to Paris exploring art museums and sidewalk cafes.',
  '1-week adventure across Iceland\'s Ring Road with waterfalls and hot springs.',
  'Budget backpacking trip through Bangkok and Chiang Mai for 8 days under $1,200.',
];

export default function App() {
  const [userQuery, setUserQuery] = useState('');
  const [threadId, setThreadId] = useState<string | null>(() => {
    return localStorage.getItem('travel_thread_id') || null;
  });
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState<'draft' | 'approval' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<TravelResponse | null>(null);
  const [feedback, setFeedback] = useState('');
  const [copied, setCopied] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [exportToast, setExportToast] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const exportDropdownRef = useRef<HTMLDivElement | null>(null);
  const [savedTrips, setSavedTrips] = useState<SavedTrip[]>(() => {
    try {
      const stored = localStorage.getItem('travel_saved_trips');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Close export menu on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        exportDropdownRef.current &&
        !exportDropdownRef.current.contains(event.target as Node)
      ) {
        setExportMenuOpen(false);
      }
    }
    if (exportMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [exportMenuOpen]);

  // Accordion details toggle states
  const [openSections, setOpenSections] = useState({
    flights: false,
    hotels: false,
    weather: false,
    budget: false,
    itinerary: false,
  });

  const resultRef = useRef<HTMLDivElement | null>(null);

  // Sync saved trips
  useEffect(() => {
    try {
      localStorage.setItem('travel_saved_trips', JSON.stringify(savedTrips));
    } catch (e) {
      console.warn('Failed to save trips to localStorage', e);
    }
  }, [savedTrips]);

  // Handle initial travel inquiry
  const handlePlanTrip = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = userQuery.trim();
    if (!query) {
      setError('Please enter your travel details or select an inspiration prompt.');
      return;
    }

    setError(null);
    setLoading(true);
    setLoadingAction('draft');

    try {
      const response = await fetch('/api/travel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          thread_id: threadId,
        }),
      });

      const data: TravelResponse = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to communicate with travel agents.');
      }

      setThreadId(data.thread_id);
      localStorage.setItem('travel_thread_id', data.thread_id);
      setCurrentPlan(data);
      setFeedback('');

      // Auto-save finalized plans if approved directly
      if (!data.requires_approval && data.guardrail_allowed && data.answer) {
        saveTripToHistory(data);
      }

      // Scroll smoothly to results
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err: any) {
      setError(err?.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
      setLoadingAction(null);
    }
  };

  // Handle Human-in-the-Loop Approval or Revision
  const handleApproval = async (approved: boolean) => {
    if (!currentPlan?.thread_id) {
      setError('No active trip session found to approve.');
      return;
    }

    if (!approved && !feedback.trim()) {
      setError('Please provide revision feedback before requesting adjustments.');
      return;
    }

    setError(null);
    setLoading(true);
    setLoadingAction('approval');

    try {
      const response = await fetch('/api/travel/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: currentPlan.thread_id,
          approved,
          feedback: feedback.trim(),
        }),
      });

      const data: TravelResponse = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to finalize trip itinerary.');
      }

      setCurrentPlan(data);
      setFeedback('');

      if (data.answer) {
        saveTripToHistory(data);
      }

      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err: any) {
      setError(err?.message || 'Could not resume agent execution.');
    } finally {
      setLoading(false);
      setLoadingAction(null);
    }
  };

  const saveTripToHistory = (plan: TravelResponse) => {
    const newTrip: SavedTrip = {
      id: `trip_${Date.now()}`,
      thread_id: plan.thread_id,
      title: plan.trip_constraints?.destination || 'Personalized Trip',
      destination: plan.trip_constraints?.destination || 'Global',
      user_query: plan.user_query,
      answer: plan.answer || '',
      flight_results: plan.flight_results || '',
      hotel_results: plan.hotel_results || '',
      weather_results: plan.weather_results || '',
      budget_results: plan.budget_results || '',
      itinerary: plan.itinerary || '',
      selected_agents: plan.selected_agents || [],
      supervisor_reasoning: plan.supervisor_reasoning || '',
      created_at: Date.now(),
    };

    setSavedTrips((prev) => {
      const filtered = prev.filter((t) => t.thread_id !== plan.thread_id);
      return [newTrip, ...filtered];
    });
  };

  const handleCopy = () => {
    if (!currentPlan?.answer) return;
    navigator.clipboard
      .writeText(currentPlan.answer)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {
        setError('Could not copy to clipboard.');
      });
  };

  const handlePrint = () => {
    window.print();
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSafeSlug = (plan: TravelResponse | SavedTrip) => {
    const dest =
      'trip_constraints' in plan && plan.trip_constraints?.destination
        ? plan.trip_constraints.destination
        : 'destination' in plan
        ? plan.destination
        : 'trip';
    return (
      dest
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '') || 'trip'
    );
  };

  const handleExportMarkdown = (plan: TravelResponse | SavedTrip) => {
    const dest =
      'trip_constraints' in plan && plan.trip_constraints?.destination
        ? plan.trip_constraints.destination
        : 'destination' in plan
        ? plan.destination
        : 'Trip';
    const duration =
      'trip_constraints' in plan && plan.trip_constraints?.duration
        ? plan.trip_constraints.duration
        : '';
    const budget =
      'trip_constraints' in plan && plan.trip_constraints?.budget
        ? plan.trip_constraints.budget
        : '';
    const style =
      'trip_constraints' in plan && plan.trip_constraints?.travel_style
        ? plan.trip_constraints.travel_style
        : '';
    const dateStr = new Date().toISOString().slice(0, 10);
    const filename = `tripmate-${getSafeSlug(plan)}-${dateStr}.md`;

    let md = `# TripMate AI Travel Itinerary: ${dest}\n\n`;
    md += `> **Export Date:** ${dateStr}\n`;
    if (duration) md += `> **Duration:** ${duration}\n`;
    if (budget) md += `> **Budget:** ${budget}\n`;
    if (style) md += `> **Travel Style:** ${style}\n`;
    md += `> **Original Request:** "${plan.user_query}"\n\n`;
    md += `---\n\n`;
    md += `${plan.answer || plan.itinerary || ''}\n\n`;

    if (plan.flight_results) {
      md += `\n---\n\n## ✈️ Flight Agent Intelligence\n\n${plan.flight_results}\n`;
    }
    if (plan.hotel_results) {
      md += `\n---\n\n## 🏨 Hotel & Lodging Suggestions\n\n${plan.hotel_results}\n`;
    }
    if (plan.weather_results) {
      md += `\n---\n\n## 🌦️ Weather & Packing Guidance\n\n${plan.weather_results}\n`;
    }
    if (plan.budget_results) {
      md += `\n---\n\n## 💰 Budget & Cost Breakdown\n\n${plan.budget_results}\n`;
    }
    md += `\n---\n*Created with TripMate AI (Offline Export)*\n`;

    downloadFile(md, filename, 'text/markdown;charset=utf-8');
    setExportToast(`Exported ${filename}`);
    setTimeout(() => setExportToast(null), 3500);
  };

  const handleExportJSON = (plan: TravelResponse | SavedTrip) => {
    const dest =
      'trip_constraints' in plan && plan.trip_constraints?.destination
        ? plan.trip_constraints.destination
        : 'destination' in plan
        ? plan.destination
        : 'Trip';
    const dateStr = new Date().toISOString().slice(0, 10);
    const filename = `tripmate-${getSafeSlug(plan)}-${dateStr}.json`;

    const exportData = {
      app: 'TripMate AI',
      version: '2.0.0',
      exported_at: new Date().toISOString(),
      thread_id: plan.thread_id,
      user_query: plan.user_query,
      destination: dest,
      constraints:
        'trip_constraints' in plan
          ? plan.trip_constraints
          : { destination: dest },
      supervisor_reasoning: plan.supervisor_reasoning,
      selected_agents: plan.selected_agents,
      itinerary_markdown: plan.answer || plan.itinerary || '',
      specialist_intelligence: {
        flight_results: plan.flight_results || '',
        hotel_results: plan.hotel_results || '',
        weather_results: plan.weather_results || '',
        budget_results: plan.budget_results || '',
      },
    };

    downloadFile(
      JSON.stringify(exportData, null, 2),
      filename,
      'application/json;charset=utf-8'
    );
    setExportToast(`Exported ${filename}`);
    setTimeout(() => setExportToast(null), 3500);
  };

  const handleResetTrip = () => {
    setCurrentPlan(null);
    setUserQuery('');
    setFeedback('');
    setError(null);
    setThreadId(null);
    localStorage.removeItem('travel_thread_id');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const loadPastTrip = (trip: SavedTrip) => {
    setCurrentPlan({
      success: true,
      thread_id: trip.thread_id,
      user_query: trip.user_query,
      guardrail_allowed: true,
      selected_agents: trip.selected_agents,
      trip_constraints: {
        destination: trip.destination,
        origin: '',
        duration: '',
        budget: '',
        travel_style: '',
        special_preferences: [],
      },
      supervisor_reasoning: trip.supervisor_reasoning,
      requires_approval: false,
      answer: trip.answer,
      flight_results: trip.flight_results,
      hotel_results: trip.hotel_results,
      weather_results: trip.weather_results,
      budget_results: trip.budget_results,
      itinerary: trip.itinerary,
    });
    setThreadId(trip.thread_id);
    setUserQuery(trip.user_query);
    setShowHistory(false);
    setTimeout(() => {
      resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const toggleSection = (key: keyof typeof openSections) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const renderMarkdown = (content: string) => {
    try {
      return { __html: marked.parse(content || '') as string };
    } catch {
      return { __html: content };
    }
  };

  return (
    <div className="relative min-h-screen text-slate-100 pb-16">
      {/* Background radial gradients */}
      <div className="page-bg" />
      <div className="gradient-circle circle-1" />
      <div className="gradient-circle circle-2" />
      <div className="gradient-circle circle-3" />

      {/* Topbar Navigation */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[#07111f]/80 border-b border-slate-800/80 px-4 sm:px-8 py-3.5 no-print">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-2 group text-white font-bold text-lg sm:text-xl tracking-tight">
              <span className="w-8 h-8 rounded-lg bg-teal-500/20 border border-teal-500/40 text-teal-400 flex items-center justify-center font-bold text-lg shadow-sm shadow-teal-500/20 group-hover:scale-105 transition-transform">
                ✳
              </span>
              <span>
                tripmate<span className="text-teal-400">.ai</span>
              </span>
            </a>
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
              Your AI travel companion
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setShowHistory(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium text-slate-300 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 transition"
              title="View past trip plans"
            >
              <History className="w-3.5 h-3.5 text-teal-400" />
              <span>Saved Trips</span>
              {savedTrips.length > 0 && (
                <span className="px-1.5 py-0.2 bg-teal-500/30 text-teal-300 rounded-full font-mono text-[10px]">
                  {savedTrips.length}
                </span>
              )}
            </button>
            {currentPlan && (
              <button
                onClick={handleResetTrip}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800/60 border border-slate-700/60 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                New Trip
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-10 sm:pt-14 space-y-8">
        {/* Hero Section */}
        <section className="text-center space-y-4 no-print">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-teal-950/60 border border-teal-500/30 text-teal-300 text-xs font-semibold tracking-wider uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
            LESS PLANNING, MORE WANDERING
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Your next trip,<br />
            <span className="bg-gradient-to-r from-teal-300 via-sky-300 to-purple-300 bg-clip-text text-transparent">
              thoughtfully planned.
            </span>
          </h1>

          <p className="max-w-xl mx-auto text-sm sm:text-base text-slate-300/90 leading-relaxed">
            Tell us what you have in mind. We’ll coordinate specialized agents for flights, stays, weather, budget, and a custom day-by-day itinerary.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 pt-2 text-xs sm:text-sm text-slate-300 font-medium">
            <span className="flex items-center gap-1.5">
              <Plane className="w-4 h-4 text-sky-400" /> Flight ideas
            </span>
            <span className="flex items-center gap-1.5">
              <Building className="w-4 h-4 text-amber-400" /> Places to stay
            </span>
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-teal-400" /> Personal itinerary
            </span>
          </div>
        </section>

        {/* Form Card */}
        <section className="relative rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur-xl p-5 sm:p-8 no-print">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-5">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-widest text-teal-400">Start Your Journey</p>
              <h2 className="text-xl sm:text-2xl font-bold text-white mt-0.5">Where to next?</h2>
            </div>
            <div className="w-8 h-8 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 flex items-center justify-center font-bold">
              ↗
            </div>
          </div>

          <form onSubmit={handlePlanTrip} className="space-y-4">
            <div>
              <label htmlFor="trip-message" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Describe your trip
              </label>
              <textarea
                id="trip-message"
                rows={4}
                value={userQuery}
                onChange={(e) => setUserQuery(e.target.value)}
                placeholder="For example: Plan a 5-day trip to Tokyo in April for two people, with great food and a moderate budget."
                className="w-full rounded-xl bg-slate-950/80 border border-slate-700/80 p-3.5 text-sm sm:text-base text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition resize-none leading-relaxed"
                required
              />
              <p className="mt-2 text-xs text-slate-400">
                Destination, dates, budget, travel style — share whatever you know.
              </p>
            </div>

            {/* Prompt Suggestions */}
            <div className="space-y-1.5">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Quick Inspirations:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((suggestion, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => setUserQuery(suggestion)}
                    className="text-xs text-left px-2.5 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/60 text-slate-300 transition hover:text-white"
                  >
                    ✦ {suggestion.split(' ')[2]} {suggestion.split(' ')[3]}...
                  </button>
                ))}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs sm:text-sm flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-sky-600 hover:from-teal-400 hover:to-sky-500 text-slate-950 font-bold text-sm sm:text-base flex items-center justify-center gap-2 shadow-lg shadow-teal-500/20 disabled:opacity-50 transition cursor-pointer"
            >
              {loading && loadingAction === 'draft' ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Agents Planning Trip...</span>
                </>
              ) : (
                <>
                  <span>Plan my trip</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-4 pt-4 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center gap-1.5">
            <span className="text-teal-400">✧</span> A little inspiration goes a long way.
          </p>
        </section>

        {/* Workflow & Multi-Agent Status */}
        {currentPlan && (
          <section className="rounded-2xl bg-slate-900/70 border border-slate-800/90 p-5 sm:p-6 backdrop-blur-xl space-y-4 no-print">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-teal-400" />
                <h3 className="font-bold text-white text-base">Multi-Agent Workflow Execution</h3>
              </div>
              <div>
                {currentPlan.guardrail_allowed ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Guardrail passed
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                    Guardrail blocked
                  </span>
                )}
              </div>
            </div>

            {/* Supervisor reasoning */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs sm:text-sm text-slate-300 space-y-1">
              <span className="text-[11px] font-bold text-teal-400 uppercase tracking-wider block">
                Supervisor Routing Logic:
              </span>
              <p className="leading-relaxed">{currentPlan.supervisor_reasoning}</p>
            </div>

            {/* Selected Specialist Agents */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Active Specialist Agents:
              </span>
              <div className="flex flex-wrap gap-2">
                {(currentPlan.selected_agents || []).map((agentName) => {
                  const meta = AGENT_META[agentName] || {
                    label: agentName,
                    icon: Sparkles,
                    color: 'text-slate-300 border-slate-700 bg-slate-800',
                  };
                  const Icon = meta.icon;
                  return (
                    <div
                      key={agentName}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold shadow-sm ${meta.color}`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span>{meta.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Constraints */}
            {currentPlan.trip_constraints && currentPlan.trip_constraints.destination && (
              <div className="pt-2 flex flex-wrap gap-2 text-xs">
                <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
                  📍 <strong>Destination:</strong> {currentPlan.trip_constraints.destination}
                </span>
                {currentPlan.trip_constraints.duration && (
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
                    ⏳ <strong>Duration:</strong> {currentPlan.trip_constraints.duration}
                  </span>
                )}
                {currentPlan.trip_constraints.budget && (
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
                    💰 <strong>Budget:</strong> {currentPlan.trip_constraints.budget}
                  </span>
                )}
              </div>
            )}
          </section>
        )}

        {/* Human-in-the-Loop Review Section */}
        {currentPlan && currentPlan.requires_approval && (
          <section className="rounded-2xl bg-amber-950/20 border border-amber-500/30 p-5 sm:p-7 backdrop-blur-xl space-y-4 no-print shadow-xl">
            <div className="flex items-center gap-2.5 text-amber-400">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <h3 className="font-bold text-base sm:text-lg">Review Preliminary Draft Itinerary</h3>
            </div>

            <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
              {currentPlan.approval_request ||
                'Please review the draft travel plan. You can approve it as is to synthesize the final comprehensive plan, or provide revision feedback to refine it.'}
            </p>

            <div className="space-y-2">
              <label htmlFor="approval-feedback" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Optional: Request specific revisions or additions
              </label>
              <textarea
                id="approval-feedback"
                rows={2}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="e.g. Include vegetarian street food, adjust for a tighter budget, add more hiking or art galleries..."
                className="w-full rounded-xl bg-slate-950/80 border border-slate-700 p-3 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => handleApproval(true)}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs sm:text-sm shadow-md shadow-teal-500/20 disabled:opacity-50 transition cursor-pointer"
              >
                {loading && loadingAction === 'approval' ? (
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4" />
                )}
                Approve Plan & Finalize
              </button>

              <button
                type="button"
                onClick={() => handleApproval(false)}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-amber-500/30 text-amber-300 font-semibold text-xs sm:text-sm disabled:opacity-50 transition cursor-pointer"
              >
                <RotateCcw className="w-4 h-4" />
                Request Revisions
              </button>
            </div>
          </section>
        )}

        {/* Results Section */}
        {currentPlan && (
          <section ref={resultRef} className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3 no-print">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-widest text-teal-400">Made For Your Journey</p>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
                  {currentPlan.requires_approval ? 'Draft Travel Plan' : 'Your Complete Travel Plan'}
                </h2>
              </div>
              <button
                onClick={handleResetTrip}
                className="text-xs text-teal-400 hover:text-teal-300 flex items-center gap-1 font-semibold"
              >
                Plan another trip <span aria-hidden="true">↗</span>
              </button>
            </div>

            {/* Result Card */}
            <div className="rounded-2xl bg-slate-900/90 border border-slate-800 shadow-2xl backdrop-blur-2xl p-5 sm:p-8 space-y-6">
              {/* Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800 no-print">
                <span className="flex items-center gap-2 text-[11px] font-bold tracking-wider uppercase text-slate-300">
                  <span className="w-2 h-2 rounded-full bg-teal-400"></span>
                  {currentPlan.requires_approval ? 'DRAFT PREVIEW' : 'YOUR PERSONALIZED PLAN'}
                </span>

                <div className="flex items-center gap-2">
                  {/* Export Dropdown */}
                  <div className="relative" ref={exportDropdownRef}>
                    <button
                      type="button"
                      onClick={() => setExportMenuOpen((prev) => !prev)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/40 text-xs font-semibold text-teal-300 transition cursor-pointer"
                      title="Export itinerary for offline use"
                    >
                      <Download className="w-3.5 h-3.5 text-teal-400" />
                      <span>Export</span>
                      <ChevronDown
                        className={`w-3 h-3 text-teal-400 transition-transform ${
                          exportMenuOpen ? 'rotate-180' : ''
                        }`}
                      />
                    </button>

                    {exportMenuOpen && (
                      <div className="absolute right-0 mt-1.5 w-56 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl py-1.5 z-30 animate-in fade-in zoom-in-95 duration-150">
                        <div className="px-3 py-1 border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                          Export for Offline Use
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            handleExportMarkdown(currentPlan);
                            setExportMenuOpen(false);
                          }}
                          className="w-full flex items-start gap-2.5 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-800/80 hover:text-white transition cursor-pointer"
                        >
                          <FileText className="w-4 h-4 text-teal-400 mt-0.5 shrink-0" />
                          <div>
                            <div className="font-semibold text-slate-100 flex items-center gap-1.5">
                              Markdown (.md)
                            </div>
                            <div className="text-[11px] text-slate-400">
                              Formatted for Obsidian, Notion & text readers
                            </div>
                          </div>
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            handleExportJSON(currentPlan);
                            setExportMenuOpen(false);
                          }}
                          className="w-full flex items-start gap-2.5 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-800/80 hover:text-white transition cursor-pointer"
                        >
                          <FileCode className="w-4 h-4 text-sky-400 mt-0.5 shrink-0" />
                          <div>
                            <div className="font-semibold text-slate-100 flex items-center gap-1.5">
                              JSON Data (.json)
                            </div>
                            <div className="text-[11px] text-slate-400">
                              Structured raw data & specialist records
                            </div>
                          </div>
                        </button>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 transition"
                  >
                    <Copy className="w-3.5 h-3.5 text-teal-400" />
                    <span>{copied ? 'Copied!' : 'Copy plan'}</span>
                  </button>

                  <button
                    onClick={handlePrint}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 transition"
                  >
                    <Printer className="w-3.5 h-3.5 text-teal-400" />
                    <span>Print / PDF</span>
                  </button>
                </div>
              </div>

              {/* Main Itinerary Content */}
              <div
                className="prose-custom max-w-none text-slate-200 text-sm sm:text-base leading-relaxed"
                dangerouslySetInnerHTML={renderMarkdown(currentPlan.answer || '')}
              />

              {/* Collapsible Specialist Details */}
              <div className="pt-6 border-t border-slate-800/80 space-y-3 no-print">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Specialist Intelligence Breakdown
                </h4>

                {/* Flights */}
                {currentPlan.flight_results && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
                    <button
                      type="button"
                      onClick={() => toggleSection('flights')}
                      className="w-full flex items-center justify-between px-4 py-3 text-left text-xs sm:text-sm font-semibold text-slate-200 hover:bg-slate-900/60 transition"
                    >
                      <span className="flex items-center gap-2 text-sky-400">
                        <Plane className="w-4 h-4" /> Flight Search Details
                      </span>
                      {openSections.flights ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    {openSections.flights && (
                      <div
                        className="px-4 pb-4 pt-1 text-xs sm:text-sm text-slate-300 prose-custom border-t border-slate-800/60"
                        dangerouslySetInnerHTML={renderMarkdown(currentPlan.flight_results)}
                      />
                    )}
                  </div>
                )}

                {/* Hotels */}
                {currentPlan.hotel_results && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
                    <button
                      type="button"
                      onClick={() => toggleSection('hotels')}
                      className="w-full flex items-center justify-between px-4 py-3 text-left text-xs sm:text-sm font-semibold text-slate-200 hover:bg-slate-900/60 transition"
                    >
                      <span className="flex items-center gap-2 text-amber-400">
                        <Building className="w-4 h-4" /> Hotel & Accommodation Suggestions
                      </span>
                      {openSections.hotels ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    {openSections.hotels && (
                      <div
                        className="px-4 pb-4 pt-1 text-xs sm:text-sm text-slate-300 prose-custom border-t border-slate-800/60"
                        dangerouslySetInnerHTML={renderMarkdown(currentPlan.hotel_results)}
                      />
                    )}
                  </div>
                )}

                {/* Weather & Packing */}
                {currentPlan.weather_results && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
                    <button
                      type="button"
                      onClick={() => toggleSection('weather')}
                      className="w-full flex items-center justify-between px-4 py-3 text-left text-xs sm:text-sm font-semibold text-slate-200 hover:bg-slate-900/60 transition"
                    >
                      <span className="flex items-center gap-2 text-emerald-400">
                        <CloudSun className="w-4 h-4" /> Weather & Packing Checklist
                      </span>
                      {openSections.weather ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    {openSections.weather && (
                      <div
                        className="px-4 pb-4 pt-1 text-xs sm:text-sm text-slate-300 prose-custom border-t border-slate-800/60"
                        dangerouslySetInnerHTML={renderMarkdown(currentPlan.weather_results)}
                      />
                    )}
                  </div>
                )}

                {/* Budget */}
                {currentPlan.budget_results && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
                    <button
                      type="button"
                      onClick={() => toggleSection('budget')}
                      className="w-full flex items-center justify-between px-4 py-3 text-left text-xs sm:text-sm font-semibold text-slate-200 hover:bg-slate-900/60 transition"
                    >
                      <span className="flex items-center gap-2 text-purple-400">
                        <Wallet className="w-4 h-4" /> Budget Feasibility Breakdown
                      </span>
                      {openSections.budget ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    {openSections.budget && (
                      <div
                        className="px-4 pb-4 pt-1 text-xs sm:text-sm text-slate-300 prose-custom border-t border-slate-800/60"
                        dangerouslySetInnerHTML={renderMarkdown(currentPlan.budget_results)}
                      />
                    )}
                  </div>
                )}

                {/* Itinerary */}
                {currentPlan.itinerary && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
                    <button
                      type="button"
                      onClick={() => toggleSection('itinerary')}
                      className="w-full flex items-center justify-between px-4 py-3 text-left text-xs sm:text-sm font-semibold text-slate-200 hover:bg-slate-900/60 transition"
                    >
                      <span className="flex items-center gap-2 text-teal-400">
                        <Calendar className="w-4 h-4" /> Day-by-Day Detailed Schedule
                      </span>
                      {openSections.itinerary ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    {openSections.itinerary && (
                      <div
                        className="px-4 pb-4 pt-1 text-xs sm:text-sm text-slate-300 prose-custom border-t border-slate-800/60"
                        dangerouslySetInnerHTML={renderMarkdown(currentPlan.itinerary)}
                      />
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Bottom Note */}
        <section className="text-center py-8 space-y-2 text-slate-400 no-print">
          <div className="w-8 h-8 mx-auto rounded-full bg-teal-500/10 text-teal-400 flex items-center justify-center font-bold">
            ✳
          </div>
          <p className="text-sm font-medium text-slate-300">Good trips start with a little curiosity.</p>
          <span className="text-xs text-slate-500 font-mono tracking-widest">✦ &nbsp;✧ &nbsp;✦</span>
        </section>
      </main>

      {/* Saved Trips Drawer / Modal */}
      {showHistory && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm no-print">
          <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full p-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                <div className="flex items-center gap-2">
                  <Bookmark className="w-5 h-5 text-teal-400" />
                  <h3 className="font-bold text-lg text-white">Saved Travel Plans</h3>
                </div>
                <button
                  onClick={() => setShowHistory(false)}
                  className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {savedTrips.length === 0 ? (
                <div className="text-center py-12 text-slate-400 space-y-2">
                  <Compass className="w-10 h-10 mx-auto text-slate-600" />
                  <p className="text-sm font-medium">No saved trips yet.</p>
                  <p className="text-xs text-slate-500">Plan a trip and your itineraries will be automatically remembered here.</p>
                </div>
              ) : (
                <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-220px)] pr-1">
                  {savedTrips.map((trip) => (
                    <div
                      key={trip.id}
                      onClick={() => loadPastTrip(trip)}
                      className="p-4 rounded-xl bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800 hover:border-teal-500/50 cursor-pointer transition space-y-2 group"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-sm text-white group-hover:text-teal-300 transition">
                          {trip.title}
                        </h4>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(trip.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">{trip.user_query}</p>

                      <div className="flex items-center justify-between pt-1.5 border-t border-slate-800/80 text-[11px]">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                          Offline Export:
                        </span>
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleExportMarkdown(trip);
                            }}
                            className="px-2 py-0.5 rounded bg-slate-800/90 hover:bg-teal-500/20 border border-slate-700 hover:border-teal-500/40 text-teal-400 hover:text-teal-300 flex items-center gap-1 font-mono text-[10px] transition cursor-pointer"
                            title="Export Markdown (.md)"
                          >
                            <FileText className="w-3 h-3" /> .md
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleExportJSON(trip);
                            }}
                            className="px-2 py-0.5 rounded bg-slate-800/90 hover:bg-sky-500/20 border border-slate-700 hover:border-sky-500/40 text-sky-400 hover:text-sky-300 flex items-center gap-1 font-mono text-[10px] transition cursor-pointer"
                            title="Export JSON (.json)"
                          >
                            <FileCode className="w-3 h-3" /> .json
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {savedTrips.length > 0 && (
              <div className="pt-4 border-t border-slate-800">
                <button
                  onClick={() => {
                    setSavedTrips([]);
                    localStorage.removeItem('travel_saved_trips');
                  }}
                  className="w-full py-2 text-xs text-rose-400 hover:text-rose-300 font-medium transition text-center"
                >
                  Clear saved history
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {exportToast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2.5 rounded-full bg-slate-900/95 border border-teal-500/50 text-teal-300 text-xs sm:text-sm font-semibold shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-bottom-2 duration-200">
          <Check className="w-4 h-4 text-teal-400" />
          <span>{exportToast}</span>
        </div>
      )}

      {/* Footer */}
      <footer className="max-w-4xl mx-auto px-4 sm:px-6 pt-10 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2 no-print">
        <span className="font-semibold text-slate-400">tripmate.ai</span>
        <span>Thoughtful travel starts here.</span>
      </footer>
    </div>
  );
}
