'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, CheckCircle2, AlertCircle, Clock, Calendar } from 'lucide-react';
import { Analytics } from '@/types/task';
import { getAnalytics } from '@/lib/api';
import { formatNumber, formatDuration, cn } from '@/lib/utils';
import AnalyticsChart from '@/components/AnalyticsChart';

/**
 * Analytics dashboard page with comprehensive metrics and visualizations
 */
export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getAnalytics();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setError('Failed to load analytics data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-32 w-full rounded-lg" />
          ))}
        </div>
        <div className="skeleton h-96 w-full rounded-lg" />
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="w-16 h-16 text-danger-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to Load Analytics</h2>
        <p className="text-gray-600 mb-4">{error || 'An unexpected error occurred'}</p>
        <button
          onClick={loadAnalytics}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Prepare chart data
  const completionTimelineData = analytics.completion_timeline.map((item) => ({
    name: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: item.completed,
  }));

  const productivityTrendData = analytics.productivity_trend.map((item) => ({
    name: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    completed: item.completed,
    created: item.created,
  }));

  const deadlineAdherenceData = [
    { name: 'On Time', value: analytics.deadline_adherence.on_time },
    { name: 'Late', value: analytics.deadline_adherence.late },
    { name: 'Pending', value: analytics.deadline_adherence.pending },
  ];

  const statCards = [
    {
      title: 'Total Tasks',
      value: formatNumber(analytics.total_tasks),
      icon: TrendingUp,
      color: 'primary',
      bgColor: 'bg-primary-50',
      textColor: 'text-primary-600',
      borderColor: 'border-primary-200',
    },
    {
      title: 'Completion Rate',
      value: `${analytics.completion_rate.toFixed(1)}%`,
      subtitle: `${formatNumber(analytics.completed_tasks)} completed`,
      icon: CheckCircle2,
      color: 'success',
      bgColor: 'bg-success-50',
      textColor: 'text-success-600',
      borderColor: 'border-success-200',
    },
    {
      title: 'On-Time Rate',
      value: `${analytics.on_time_completion_rate.toFixed(1)}%`,
      subtitle: 'Deadline adherence',
      icon: Clock,
      color: 'warning',
      bgColor: 'bg-warning-50',
      textColor: 'text-warning-600',
      borderColor: 'border-warning-200',
    },
    {
      title: 'Avg Delay',
      value: analytics.average_delay_hours
        ? formatDuration(analytics.average_delay_hours)
        : 'N/A',
      subtitle: 'For late tasks',
      icon: AlertCircle,
      color: 'danger',
      bgColor: 'bg-danger-50',
      textColor: 'text-danger-600',
      borderColor: 'border-danger-200',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Track your productivity trends and performance metrics
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className={cn(
                'bg-white rounded-lg shadow-md border-2 p-6',
                stat.borderColor
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 mb-1">{stat.title}</p>
                  <p className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</p>
                  {stat.subtitle && (
                    <p className={cn('text-xs font-medium', stat.textColor)}>
                      {stat.subtitle}
                    </p>
                  )}
                </div>
                <div className={cn('p-3 rounded-lg', stat.bgColor)}>
                  <Icon className={cn('w-6 h-6', stat.textColor)} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Completion Timeline */}
        {completionTimelineData.length > 0 && (
          <AnalyticsChart
            data={completionTimelineData}
            type="line"
            dataKey="value"
            xKey="name"
            title="Completion Timeline"
            colors={['#22c55e']}
            height={300}
          />
        )}

        {/* Deadline Adherence */}
        {deadlineAdherenceData.some((d) => d.value > 0) && (
          <AnalyticsChart
            data={deadlineAdherenceData}
            type="pie"
            dataKey="value"
            xKey="name"
            title="Deadline Adherence"
            colors={['#22c55e', '#ef4444', '#f59e0b']}
            height={300}
          />
        )}
      </div>

      {/* Productivity Trend */}
      {productivityTrendData.length > 0 && (
        <div className="bg-white rounded-lg p-6 shadow-md border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Productivity Trend</h3>
          <div className="h-80">
            <AnalyticsChart
              data={productivityTrendData}
              type="bar"
              dataKey="completed"
              xKey="name"
              colors={['#3b82f6']}
              height={320}
            />
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {analytics.recent_activity && analytics.recent_activity.length > 0 && (
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Calendar className="w-6 h-6 text-primary-600" />
            Recent Activity
          </h2>
          <div className="space-y-3">
            {analytics.recent_activity.map((activity) => {
              const getActivityIcon = () => {
                switch (activity.action) {
                  case 'completed':
                    return <CheckCircle2 className="w-5 h-5 text-success-600" />;
                  case 'overdue':
                    return <AlertCircle className="w-5 h-5 text-danger-600" />;
                  case 'created':
                    return <TrendingUp className="w-5 h-5 text-primary-600" />;
                  default:
                    return <Clock className="w-5 h-5 text-warning-600" />;
                }
              };

              const getActivityColor = () => {
                switch (activity.action) {
                  case 'completed':
                    return 'bg-success-50 border-success-200';
                  case 'overdue':
                    return 'bg-danger-50 border-danger-200';
                  case 'created':
                    return 'bg-primary-50 border-primary-200';
                  default:
                    return 'bg-warning-50 border-warning-200';
                }
              };

              return (
                <div
                  key={activity.id}
                  className={cn(
                    'flex items-start gap-3 p-4 rounded-lg border-2',
                    getActivityColor()
                  )}
                >
                  <div className="flex-shrink-0 mt-0.5">{getActivityIcon()}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">
                      {activity.task_title}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {activity.action.charAt(0).toUpperCase() + activity.action.slice(1)} •{' '}
                      {new Date(activity.timestamp).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                    </p>
                    {activity.details && (
                      <p className="text-xs text-gray-500 mt-1">{activity.details}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* No Data Message */}
      {analytics.total_tasks === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analytics Data</h3>
          <p className="text-gray-600">Create some tasks to see your analytics and insights.</p>
        </div>
      )}
    </div>
  );
}
