import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ComposedChart, ReferenceLine
} from 'recharts';
import {
  Settings, Plus, Trash2, Calendar, Zap, Filter, Download, RefreshCw,
  TrendingUp, TrendingDown, ChevronDown, ChevronRight, AlertCircle,
  CheckCircle, AlertTriangle, Eye, EyeOff, Link2, Loader, FileText,
  FileJson, FileSpreadsheet, Info, Clock, Activity, Target
} from 'lucide-react';

// ========================
// API Client
// ========================

const API_BASE = 'http://localhost:8000/api';

const api = {
  getStatus: () => fetch(`${API_BASE}/status`).then(r => r.json()),
  getTags: () => fetch(`${API_BASE}/tags`).then(r => r.json()),
  addTag: (tag) => fetch(`${API_BASE}/tags`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tag })
  }).then(r => r.json()),
  removeTag: (tag) => fetch(`${API_BASE}/tags/${tag}`, { method: 'DELETE' }).then(r => r.json()),
  getLatestRun: () => fetch(`${API_BASE}/run/latest`).then(r => r.json()).catch(() => null),
  triggerRun: (tags, date_range_days, intervention_date, force_refresh) =>
    fetch(`${API_BASE}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags, date_range_days, intervention_date, force_refresh })
    }).then(r => r.json()),
  getRunStatus: (run_id) => fetch(`${API_BASE}/run/${run_id}/status`).then(r => r.json()),
  getSuggestions: (tag, min_confidence, verified_only) =>
    fetch(`${API_BASE}/suggestions?tag=${tag || ''}&min_confidence=${min_confidence}&verified_only=${verified_only}`)
      .then(r => r.json()),
  getComparison: (tag) => fetch(`${API_BASE}/comparison/${tag}`).then(r => r.json()).catch(() => null),
  getLatestReports: () => fetch(`${API_BASE}/reports/latest`).then(r => r.json())
};

// ========================
// Constants
// ========================

const COLORS = {
  bg: '#0A0F1E',
  sidebar: '#101629',
  card: '#151D33',
  border: '#2d3a52',
  accent: '#00D4FF',
  success: '#00FF88',
  warning: '#FFB800',
  error: '#FF4444',
  text: '#E8ECFF',
  textSecondary: '#B0B8D4'
};

const STATUS_COLORS = {
  IDLE: '#00FF88',
  RUNNING: '#00D4FF',
  ERROR: '#FF4444'
};

const VERIFICATION_COLORS = {
  VERIFIED: '#00FF88',
  UNVERIFIED: '#FF4444',
  LOW_CONFIDENCE: '#FFB800'
};

// ========================
// Utility Components
// ========================

const TrendArrow = ({ trend, pct }) => {
  if (trend === 'up' || pct > 0) return <TrendingUp size={16} className="text-green-400" />;
  if (trend === 'down' || pct < 0) return <TrendingDown size={16} className="text-red-400" />;
  return <div className="w-4 h-4" />;
};

const Badge = ({ children, variant = 'default', className = '' }) => {
  const variants = {
    default: 'bg-blue-900 text-blue-100',
    success: 'bg-green-900 text-green-100',
    warning: 'bg-amber-900 text-amber-100',
    error: 'bg-red-900 text-red-100',
    info: 'bg-indigo-900 text-indigo-100'
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

const PulsingDot = ({ color = 'bg-green-400' }) => (
  <span className={`inline-block w-2 h-2 ${color} rounded-full animate-pulse mr-2`} />
);

const Skeleton = ({ w = 'w-full', h = 'h-4', className = '' }) => (
  <div className={`${w} ${h} ${className} bg-gray-700 rounded animate-pulse`} />
);

// ========================
// Sidebar Components
// ========================

const TagManager = ({ tags, onTagAdd, onTagRemove }) => {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAdd = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.addTag(input);
      if (res.valid) {
        onTagAdd(input);
        setInput('');
      } else {
        setError(res.suggestion || 'Invalid tag');
      }
    } catch (e) {
      setError('Error adding tag');
    }
    setLoading(false);
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">Tags</h3>
      <div className="flex flex-wrap gap-2">
        {tags.map(tag => (
          <div key={tag} className="flex items-center gap-1 bg-blue-900 text-blue-100 px-2 py-1 rounded text-xs">
            <span>{tag}</span>
            <button
              onClick={() => onTagRemove(tag)}
              className="hover:text-red-400 transition"
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>
      <div className="flex gap-1">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          placeholder="Add tag..."
          className="flex-1 bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 focus:border-blue-400 focus:outline-none"
        />
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition disabled:opacity-50"
        >
          <Plus size={14} />
        </button>
      </div>
      {error && <p className="text-red-400 text-xs">{error}</p>}
    </div>
  );
};

const DateRangePicker = ({ selectedRange, onRangeChange }) => {
  const ranges = [
    { label: '7d', days: 7 },
    { label: '30d', days: 30 },
    { label: '90d', days: 90 },
    { label: '1Y', days: 365 }
  ];

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">Date Range</h3>
      <div className="grid grid-cols-4 gap-1">
        {ranges.map(r => (
          <button
            key={r.days}
            onClick={() => onRangeChange(r.days)}
            className={`px-2 py-1 rounded text-xs font-medium transition ${
              selectedRange === r.days
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>
    </div>
  );
};

const InterventionDatePicker = ({ value, onChange, onClear }) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">Intervention Date</h3>
        <div className="group relative">
          <Info size={14} className="text-gray-500 cursor-help" />
          <div className="hidden group-hover:block absolute bottom-full left-0 mb-1 bg-gray-800 text-gray-200 text-xs p-2 rounded w-48 z-10 border border-gray-600">
            Set the date when a solution was deployed to compare before/after metrics
          </div>
        </div>
      </div>
      <div className="flex gap-1">
        <input
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 focus:border-blue-400 focus:outline-none"
        />
        {value && (
          <button
            onClick={onClear}
            className="bg-red-900 hover:bg-red-800 text-red-100 px-2 py-1 rounded text-xs transition"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
};

const FilterControls = ({ filters, onFilterChange }) => {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">Filters</h3>

      <div>
        <label className="text-xs text-gray-400">Min Confidence: {filters.minConfidence}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={filters.minConfidence}
          onChange={(e) => onFilterChange({ ...filters, minConfidence: parseInt(e.target.value) })}
          className="w-full h-2 bg-gray-700 rounded appearance-none cursor-pointer"
        />
      </div>

      <div>
        <label className="text-xs text-gray-400">Answer Score: {filters.minScore}</label>
        <input
          type="range"
          min="0"
          max="50"
          value={filters.minScore}
          onChange={(e) => onFilterChange({ ...filters, minScore: parseInt(e.target.value) })}
          className="w-full h-2 bg-gray-700 rounded appearance-none cursor-pointer"
        />
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.verifiedOnly}
          onChange={(e) => onFilterChange({ ...filters, verifiedOnly: e.target.checked })}
          className="w-4 h-4"
        />
        <span className="text-xs text-gray-300">Verified Only</span>
      </label>

      <div>
        <label className="text-xs text-gray-400 block mb-1">Sort by</label>
        <select
          value={filters.sortBy}
          onChange={(e) => onFilterChange({ ...filters, sortBy: e.target.value })}
          className="w-full bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600"
        >
          <option value="confidence">Confidence</option>
          <option value="recency">Recent</option>
          <option value="impact">Impact</option>
        </select>
      </div>
    </div>
  );
};

const RefreshControls = ({ quota, onRefresh, autoRefresh, onAutoRefreshChange, onIntervalChange }) => {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">Controls</h3>

      <button
        onClick={onRefresh}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-xs font-medium transition flex items-center justify-center gap-2"
      >
        <RefreshCw size={14} />
        Refresh Now
      </button>

      <div className="space-y-2">
        <label className="text-xs text-gray-400">Quota: {quota.used}/{quota.total}</label>
        <div className="w-full bg-gray-700 rounded h-2">
          <div
            className="h-full bg-blue-500 rounded"
            style={{ width: `${(quota.used / quota.total) * 100}%` }}
          />
        </div>
        <p className="text-xs text-gray-500">{quota.remaining} calls remaining</p>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={autoRefresh}
          onChange={(e) => onAutoRefreshChange(e.target.checked)}
          className="w-4 h-4"
        />
        <span className="text-xs text-gray-300">Auto-refresh</span>
      </label>

      {autoRefresh && (
        <select
          onChange={(e) => onIntervalChange(parseInt(e.target.value))}
          defaultValue="300"
          className="w-full bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600"
        >
          <option value="60">Every 1 min</option>
          <option value="300">Every 5 min</option>
          <option value="600">Every 10 min</option>
          <option value="1800">Every 30 min</option>
        </select>
      )}
    </div>
  );
};

const ExportButtons = ({ onExport }) => {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">Export</h3>
      <div className="space-y-1">
        <button
          onClick={() => onExport('pdf')}
          className="w-full flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-2 rounded text-xs transition"
        >
          <FileText size={14} />
          PDF
        </button>
        <button
          onClick={() => onExport('json')}
          className="w-full flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-2 rounded text-xs transition"
        >
          <FileJson size={14} />
          JSON
        </button>
        <button
          onClick={() => onExport('csv')}
          className="w-full flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-2 rounded text-xs transition"
        >
          <FileSpreadsheet size={14} />
          CSV
        </button>
      </div>
    </div>
  );
};

// ========================
// Main Content Components
// ========================

const StatusBar = ({ status, lastUpdated, quota, activeTags }) => {
  return (
    <div className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <PulsingDot color={`bg-${STATUS_COLORS[status] === '#00FF88' ? 'green-400' : STATUS_COLORS[status] === '#00D4FF' ? 'blue-400' : 'red-400'}`} />
          <span className="text-sm font-mono">{status}</span>
        </div>
        <div className="text-xs text-gray-400">
          Updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Never'}
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-xs">
          <span className="text-gray-400">Tags: </span>
          <span className="text-blue-400 font-mono">{activeTags}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-32 h-2 bg-gray-700 rounded overflow-hidden">
            <div
              className="h-full bg-green-500"
              style={{ width: `${(quota.remaining / quota.total) * 100}%` }}
            />
          </div>
          <span className="text-xs text-gray-400 w-12 text-right">{quota.remaining}/{quota.total}</span>
        </div>
      </div>
    </div>
  );
};

const OverviewCards = ({ data = {} }) => {
  const cards = [
    { title: 'Total Questions', value: data.totalQuestions || 0, trend: 5 },
    { title: 'Unanswered Rate', value: `${data.unansweredRate || 0}%`, trend: -3 },
    { title: 'Avg Answer Time', value: data.avgAnswerTime || '24h', trend: -2 },
    { title: 'Verified Suggestions', value: data.verifiedSuggestions || 0, trend: 8 },
    { title: 'Quota Remaining', value: data.quotaRemaining || 0, trend: 0 },
    { title: 'Active Tags', value: data.activeTags || 0, trend: 0 }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      {cards.map((card, i) => (
        <div key={i} className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-blue-500 transition">
          <div className="text-xs text-gray-400 mb-2 uppercase tracking-wide">{card.title}</div>
          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-mono font-bold text-blue-400">{card.value}</div>
            <TrendArrow trend={card.trend > 0 ? 'up' : 'down'} pct={card.trend} />
          </div>
          <div className={`text-xs mt-1 ${card.trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {card.trend > 0 ? '+' : ''}{card.trend}% vs last period
          </div>
        </div>
      ))}
    </div>
  );
};

const TagHealthChart = ({ data = [] }) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-6">
      <h2 className="text-sm font-bold text-gray-200 uppercase mb-4">Tag Health</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="tag" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" />
          <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #4B5563' }} />
          <Legend />
          <Bar dataKey="questions" fill="#00D4FF" />
          <Bar dataKey="answered" fill="#00FF88" />
          <Bar dataKey="unanswered" fill="#FF4444" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

const VolumeOverTimeChart = ({ data = [], interventionDate = null }) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-6">
      <h2 className="text-sm font-bold text-gray-200 uppercase mb-4">Volume Over Time</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" />
          {interventionDate && (
            <ReferenceLine x={interventionDate} stroke="#FF4444" strokeDasharray="5 5" label="Intervention" />
          )}
          <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #4B5563' }} />
          <Legend />
          <Line type="monotone" dataKey="volume" stroke="#00D4FF" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const ErrorClusters = ({ errors = [] }) => {
  const [expandedId, setExpandedId] = useState(null);

  return (
    <div className="mb-6">
      <h2 className="text-sm font-bold text-gray-200 uppercase mb-4">Error Clusters</h2>
      <div className="space-y-2">
        {errors.length === 0 ? (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-center text-gray-400 text-xs">
            No error clusters found
          </div>
        ) : (
          errors.map((cluster, i) => (
            <div key={i} className="bg-gray-800 border border-gray-700 rounded-lg">
              <button
                onClick={() => setExpandedId(expandedId === i ? null : i)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-750 transition"
              >
                <div className="flex items-center gap-3 flex-1">
                  {expandedId === i ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <span className="text-sm font-mono">{cluster.label}</span>
                  <Badge variant="info">{cluster.count}</Badge>
                  {cluster.emerging && <Badge variant="warning">EMERGING</Badge>}
                </div>
                <TrendArrow trend={cluster.trend} />
              </button>
              {expandedId === i && (
                <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-300">
                  <p className="mb-2">{cluster.description}</p>
                  <a href={cluster.soLink} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 flex items-center gap-1">
                    <Link2 size={12} />
                    View on Stack Overflow
                  </a>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const SuggestionsPanel = ({ suggestions = [] }) => {
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [expandedId, setExpandedId] = useState(null);

  const filtered = suggestions.filter(s => {
    if (filterStatus === 'ALL') return true;
    return s.status === filterStatus;
  });

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-sm font-bold text-gray-200 uppercase">Suggestions</h2>
        <div className="flex gap-1">
          {['ALL', 'VERIFIED', 'UNVERIFIED', 'LOW_CONFIDENCE'].map(status => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-2 py-1 text-xs rounded transition ${
                filterStatus === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-center text-gray-400 text-xs">
            No suggestions found
          </div>
        ) : (
          filtered.map((s, i) => (
            <div
              key={i}
              className={`bg-gray-800 border rounded-lg overflow-hidden ${
                s.status === 'UNVERIFIED' ? 'border-red-600 border-l-4' : 'border-gray-700'
              }`}
            >
              {s.status === 'UNVERIFIED' && (
                <div className="bg-red-900 text-red-100 px-4 py-2 flex items-center gap-2 text-xs">
                  <AlertTriangle size={14} />
                  Unverified - Use with caution
                </div>
              )}

              <button
                onClick={() => setExpandedId(expandedId === i ? null : i)}
                className="w-full px-4 py-3 flex items-start justify-between hover:bg-gray-750 transition text-left"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge>{s.tag}</Badge>
                    <span className="text-xs text-gray-400 font-mono">{s.confidence_score}%</span>
                    <Badge variant={
                      s.status === 'VERIFIED' ? 'success' :
                      s.status === 'UNVERIFIED' ? 'error' :
                      'warning'
                    }>
                      {s.status}
                    </Badge>
                  </div>
                  <h3 className="text-sm font-medium text-gray-100 mb-1">{s.title}</h3>
                  <p className="text-xs text-gray-400">{s.summary}</p>
                </div>
                {expandedId === i ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>

              {expandedId === i && (
                <div className="border-t border-gray-700 px-4 py-3 space-y-3">
                  <div>
                    <h4 className="text-xs font-bold text-gray-200 uppercase mb-2">Evidence</h4>
                    <div className="space-y-1">
                      {s.evidence && s.evidence.map((e, ei) => (
                        <a
                          key={ei}
                          href={e.question_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                        >
                          <Link2 size={12} />
                          Q{e.question_id} - Score: {e.answer_score}
                          {e.is_accepted && <CheckCircle size={12} />}
                        </a>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-gray-200 uppercase mb-2">Reasoning</h4>
                    <p className="text-xs text-gray-300 leading-relaxed">{s.reasoning}</p>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-400">Confidence</span>
                      <span className="text-xs font-mono font-bold">{s.confidence_score}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-700 rounded overflow-hidden">
                      <div
                        className={`h-full ${
                          s.confidence_score >= 80 ? 'bg-green-500' :
                          s.confidence_score >= 60 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${s.confidence_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const BeforeAfterSection = ({ comparison = null }) => {
  if (!comparison) return null;

  const verdictColors = {
    IMPROVED: 'text-green-400 bg-green-900',
    NEUTRAL: 'text-yellow-400 bg-yellow-900',
    WORSENED: 'text-red-400 bg-red-900',
    INSUFFICIENT_DATA: 'text-gray-400 bg-gray-700'
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-6">
      <h2 className="text-sm font-bold text-gray-200 uppercase mb-4">Before/After Analysis</h2>

      <div className={`rounded px-4 py-2 mb-4 font-bold text-center ${verdictColors[comparison.verdict]}`}>
        {comparison.verdict}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <h3 className="text-xs font-bold text-gray-300 mb-2">Before</h3>
          <div className="space-y-1 text-xs">
            <div><span className="text-gray-400">Questions:</span> <span className="font-mono">{comparison.pre_period.question_count}</span></div>
            <div><span className="text-gray-400">Unanswered:</span> <span className="font-mono">{comparison.pre_period.unanswered_rate}%</span></div>
            <div><span className="text-gray-400">Avg Answer Time:</span> <span className="font-mono">{comparison.pre_period.avg_time_to_answer_hours}h</span></div>
          </div>
        </div>
        <div>
          <h3 className="text-xs font-bold text-gray-300 mb-2">After</h3>
          <div className="space-y-1 text-xs">
            <div><span className="text-gray-400">Questions:</span> <span className="font-mono">{comparison.post_period.question_count}</span></div>
            <div><span className="text-gray-400">Unanswered:</span> <span className="font-mono">{comparison.post_period.unanswered_rate}%</span></div>
            <div><span className="text-gray-400">Avg Answer Time:</span> <span className="font-mono">{comparison.post_period.avg_time_to_answer_hours}h</span></div>
          </div>
        </div>
      </div>

      {comparison.regressions && comparison.regressions.length > 0 && (
        <div className="mb-3">
          <h3 className="text-xs font-bold text-red-400 mb-2">Regressions</h3>
          <ul className="text-xs text-gray-300 space-y-1">
            {comparison.regressions.map((r, i) => <li key={i}>• {r}</li>)}
          </ul>
        </div>
      )}

      {comparison.resolutions && comparison.resolutions.length > 0 && (
        <div>
          <h3 className="text-xs font-bold text-green-400 mb-2">Resolutions</h3>
          <ul className="text-xs text-gray-300 space-y-1">
            {comparison.resolutions.map((r, i) => <li key={i}>• {r}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
};

const KnowledgeGapTracker = ({ gaps = [] }) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-6">
      <h2 className="text-sm font-bold text-gray-200 uppercase mb-4">Knowledge Gaps</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="px-2 py-2 text-left text-gray-400">Tag</th>
              <th className="px-2 py-2 text-left text-gray-400">Question</th>
              <th className="px-2 py-2 text-left text-gray-400">Days Open</th>
              <th className="px-2 py-2 text-left text-gray-400">Views</th>
              <th className="px-2 py-2 text-left text-gray-400">Score</th>
            </tr>
          </thead>
          <tbody>
            {gaps.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-2 py-4 text-center text-gray-500">No knowledge gaps</td>
              </tr>
            ) : (
              gaps.map((gap, i) => (
                <tr key={i} className="border-b border-gray-700 hover:bg-gray-750 transition">
                  <td className="px-2 py-2">
                    <Badge>{gap.tag}</Badge>
                  </td>
                  <td className="px-2 py-2">
                    <a href={gap.soUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">
                      {gap.title}
                    </a>
                  </td>
                  <td className="px-2 py-2 font-mono">{gap.daysOpen}</td>
                  <td className="px-2 py-2 font-mono">{gap.views}</td>
                  <td className="px-2 py-2 font-mono">{gap.score}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const StatusLog = ({ events = [] }) => {
  const [isOpen, setIsOpen] = useState(false);
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-gray-750 transition"
      >
        <div className="flex items-center gap-2">
          <Activity size={14} />
          <span className="text-sm font-bold text-gray-200 uppercase">Event Log</span>
          <Badge>{events.length}</Badge>
        </div>
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>

      {isOpen && (
        <div
          ref={logRef}
          className="max-h-64 overflow-y-auto bg-gray-900 border-t border-gray-700"
          style={{ backgroundColor: COLORS.bg }}
        >
          <div className="space-y-1 p-4">
            {events.length === 0 ? (
              <p className="text-xs text-gray-500">No events</p>
            ) : (
              events.map((event, i) => (
                <div
                  key={i}
                  className={`text-xs font-mono ${
                    event.status === 'ERROR' ? 'text-red-400' :
                    event.status === 'SUCCESS' ? 'text-green-400' :
                    'text-blue-400'
                  }`}
                >
                  [{event.timestamp}] {event.message}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ========================
// Main Dashboard Component
// ========================

export default function Dashboard() {
  const [tags, setTags] = useState([]);
  const [dateRange, setDateRange] = useState(30);
  const [interventionDate, setInterventionDate] = useState('');
  const [filters, setFilters] = useState({
    minConfidence: 0,
    minScore: 0,
    verifiedOnly: false,
    sortBy: 'confidence'
  });
  const [quota, setQuota] = useState({ total: 10000, used: 2500, remaining: 7500 });
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(300);

  const [status, setStatus] = useState('IDLE');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [latestRun, setLatestRun] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const wsRef = useRef(null);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusData, tagsData, runData] = await Promise.all([
          api.getStatus(),
          api.getTags(),
          api.getLatestRun()
        ]);

        if (statusData) {
          setStatus(statusData.agent_status);
          setQuota({
            total: 10000,
            used: 10000 - statusData.quota_remaining,
            remaining: statusData.quota_remaining
          });
        }

        if (tagsData) {
          setTags(tagsData.tags || []);
        }

        if (runData) {
          setLatestRun(runData);
          setLastUpdated(new Date());

          if (runData.suggestions) {
            setSuggestions(runData.suggestions);
          }

          if (tags.length > 0) {
            const comp = await api.getComparison(tags[0]);
            setComparison(comp);
          }
        }
      } catch (e) {
        console.error('Error fetching data:', e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        const runData = await api.getLatestRun();
        if (runData) {
          setLatestRun(runData);
          setLastUpdated(new Date());

          if (runData.suggestions) {
            setSuggestions(runData.suggestions);
          }
        }
      } catch (e) {
        console.error('Error in auto-refresh:', e);
      }
    }, autoRefreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, autoRefreshInterval]);

  // WebSocket connection
  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws/progress');

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const timestamp = new Date(message.timestamp).toLocaleTimeString();
      setEvents(prev => [...prev, { ...message, timestamp }]);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const result = await api.triggerRun(tags, dateRange, interventionDate || null, false);
      setEvents(prev => [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        message: `Triggered run: ${result.run_id}`,
        status: 'INFO'
      }]);
    } catch (e) {
      console.error('Error triggering refresh:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format) => {
    console.log(`Exporting as ${format}`);
    // Implementation would depend on backend support
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: COLORS.bg }}>
      {/* Sidebar */}
      <div
        className="w-80 border-r overflow-y-auto"
        style={{ backgroundColor: COLORS.sidebar, borderColor: COLORS.border }}
      >
        <div className="p-6 space-y-6">
          <TagManager
            tags={tags}
            onTagAdd={(tag) => setTags([...tags, tag])}
            onTagRemove={(tag) => setTags(tags.filter(t => t !== tag))}
          />

          <div className="border-t" style={{ borderColor: COLORS.border }} />

          <DateRangePicker selectedRange={dateRange} onRangeChange={setDateRange} />

          <InterventionDatePicker
            value={interventionDate}
            onChange={setInterventionDate}
            onClear={() => setInterventionDate('')}
          />

          <div className="border-t" style={{ borderColor: COLORS.border }} />

          <FilterControls filters={filters} onFilterChange={setFilters} />

          <div className="border-t" style={{ borderColor: COLORS.border }} />

          <RefreshControls
            quota={quota}
            onRefresh={handleRefresh}
            autoRefresh={autoRefresh}
            onAutoRefreshChange={setAutoRefresh}
            onIntervalChange={setAutoRefreshInterval}
          />

          <div className="border-t" style={{ borderColor: COLORS.border }} />

          <ExportButtons onExport={handleExport} />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <StatusBar
          status={status}
          lastUpdated={lastUpdated}
          quota={quota}
          activeTags={tags.length}
        />

        <div className="flex-1 overflow-y-auto pb-20">
          <div className="p-6">
            {loading ? (
              <div className="space-y-4">
                <Skeleton h="h-24" />
                <Skeleton h="h-64" />
              </div>
            ) : (
              <>
                <OverviewCards
                  data={{
                    totalQuestions: latestRun?.tag_analyses?.reduce((sum, t) => sum + (t.question_count || 0), 0) || 0,
                    unansweredRate: 32,
                    avgAnswerTime: '24h',
                    verifiedSuggestions: suggestions.filter(s => s.status === 'VERIFIED').length,
                    quotaRemaining: quota.remaining,
                    activeTags: tags.length
                  }}
                />

                <TagHealthChart
                  data={tags.map(tag => ({
                    tag,
                    questions: Math.floor(Math.random() * 100),
                    answered: Math.floor(Math.random() * 80),
                    unanswered: Math.floor(Math.random() * 20)
                  }))}
                />

                <VolumeOverTimeChart
                  data={Array.from({ length: 30 }, (_, i) => ({
                    date: new Date(Date.now() - (30 - i) * 86400000).toLocaleDateString(),
                    volume: Math.floor(Math.random() * 100 + 50)
                  }))}
                  interventionDate={interventionDate}
                />

                <ErrorClusters
                  errors={[
                    {
                      label: 'TypeScript compilation errors',
                      count: 45,
                      emerging: true,
                      trend: 'up',
                      description: 'Recent increase in TypeScript type checking failures',
                      soLink: '#'
                    }
                  ]}
                />

                <SuggestionsPanel suggestions={suggestions} />

                {comparison && interventionDate && (
                  <BeforeAfterSection comparison={comparison} />
                )}

                <KnowledgeGapTracker
                  gaps={[
                    {
                      tag: 'react',
                      title: 'How to handle async state in React hooks?',
                      daysOpen: 15,
                      views: 324,
                      score: 42,
                      soUrl: '#'
                    }
                  ]}
                />
              </>
            )}
          </div>
        </div>

        <StatusLog events={events} />
      </div>
    </div>
  );
}

export default Dashboard;
