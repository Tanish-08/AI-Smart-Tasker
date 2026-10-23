'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, TrendingUp, CheckCircle2, AlertCircle, Clock, ArrowRight } from 'lucide-react';
import { Task } from '@/types/task';
import { getTasks } from '@/lib/api';
import { calculateCompletionRate, formatNumber, cn } from '@/lib/utils';
import TaskCard from '@/components/TaskCard';
import TaskForm from '@/components/TaskForm';
import Modal from '@/components/Modal';

/**
 * Dashboard home page
 * Shows overview statistics, recent tasks, and quick actions
 */
export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    setIsLoading(true);
    try {
      const data = await getTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTaskCreated = (task: Task) => {
    setTasks([task, ...tasks]);
    setShowCreateModal(false);
  };

  const handleTaskUpdated = (updatedTask: Task) => {
    setTasks(tasks.map((t) => (t.id === updatedTask.id ? updatedTask : t)));
    setEditingTask(null);
  };

  const handleTaskDeleted = (taskId: number) => {
    setTasks(tasks.filter((t) => t.id !== taskId));
  };

  // Calculate statistics
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.completed).length;
  const pendingTasks = tasks.filter((t) => !t.completed).length;
  const overdueTasks = tasks.filter((t) => (t.is_overdue ?? false) && !t.completed).length;
  const completionRate = calculateCompletionRate(completedTasks, totalTasks);

  // Get recent tasks (5 most recent)
  const recentTasks = tasks.slice(0, 5);

  const statCards = [
    {
      title: 'Total Tasks',
      value: formatNumber(totalTasks),
      icon: TrendingUp,
      color: 'primary',
      bgColor: 'bg-primary-50',
      textColor: 'text-primary-600',
      borderColor: 'border-primary-200',
    },
    {
      title: 'Completed',
      value: formatNumber(completedTasks),
      subtitle: `${completionRate}% completion rate`,
      icon: CheckCircle2,
      color: 'success',
      bgColor: 'bg-success-50',
      textColor: 'text-success-600',
      borderColor: 'border-success-200',
    },
    {
      title: 'Pending',
      value: formatNumber(pendingTasks),
      icon: Clock,
      color: 'warning',
      bgColor: 'bg-warning-50',
      textColor: 'text-warning-600',
      borderColor: 'border-warning-200',
    },
    {
      title: 'Overdue',
      value: formatNumber(overdueTasks),
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Here&apos;s your task overview.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className={cn(
            'inline-flex items-center justify-center gap-2 px-6 py-3',
            'text-white bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg font-medium shadow-md',
            'hover:from-primary-700 hover:to-primary-800 transition-all',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2'
          )}
        >
          <Plus className="w-5 h-5" />
          Create Task
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className={cn(
                'bg-white rounded-lg shadow-md border-2 p-6 transition-transform hover:scale-105',
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

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          href="/tasks"
          className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-6 hover:border-primary-300 hover:shadow-lg transition-all group"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">View All Tasks</h3>
              <p className="text-gray-600 text-sm">
                Manage your complete task list with advanced filtering
              </p>
            </div>
            <ArrowRight className="w-6 h-6 text-primary-600 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        <Link
          href="/analytics"
          className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-6 hover:border-primary-300 hover:shadow-lg transition-all group"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">View Analytics</h3>
              <p className="text-gray-600 text-sm">
                Track your productivity trends and performance metrics
              </p>
            </div>
            <ArrowRight className="w-6 h-6 text-primary-600 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>
      </div>

      {/* Recent Tasks */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Recent Tasks</h2>
          {tasks.length > 5 && (
            <Link
              href="/tasks"
              className="text-primary-600 hover:text-primary-700 font-medium text-sm flex items-center gap-1"
            >
              View all
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="skeleton h-32 w-full" />
            ))}
          </div>
        ) : recentTasks.length > 0 ? (
          <div className="space-y-4">
            {recentTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onTaskUpdated={handleTaskUpdated}
                onTaskDeleted={handleTaskDeleted}
                onEditClick={setEditingTask}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Clock className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No tasks yet</h3>
            <p className="text-gray-600 mb-4">Create your first task to get started!</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-6 py-3 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create Task
            </button>
          </div>
        )}
      </div>

      {/* Create Task Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Task"
        size="lg"
      >
        <TaskForm onSuccess={handleTaskCreated} onCancel={() => setShowCreateModal(false)} />
      </Modal>

      {/* Edit Task Modal */}
      {editingTask && (
        <Modal
          isOpen={true}
          onClose={() => setEditingTask(null)}
          title="Edit Task"
          size="lg"
        >
          <TaskForm
            task={editingTask}
            onSuccess={handleTaskUpdated}
            onCancel={() => setEditingTask(null)}
          />
        </Modal>
      )}
    </div>
  );
}
