'use client';

import { useState } from 'react';
import { Task } from '@/types/task';
import TaskCard from './TaskCard';
import { Filter, Search, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TaskListProps {
  tasks: Task[];
  onTaskUpdated: (task: Task) => void;
  onTaskDeleted: (taskId: number) => void;
  onEditClick: (task: Task) => void;
  isLoading?: boolean;
}

type FilterOption = 'all' | 'completed' | 'pending' | 'overdue';

/**
 * TaskList component displays tasks with filtering and search capabilities
 */
export default function TaskList({
  tasks,
  onTaskUpdated,
  onTaskDeleted,
  onEditClick,
  isLoading = false,
}: TaskListProps) {
  const [activeFilter, setActiveFilter] = useState<FilterOption>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter tasks based on active filter and search query
  const filteredTasks = tasks.filter((task) => {
    // Apply filter
    let matchesFilter = true;
    switch (activeFilter) {
      case 'completed':
        matchesFilter = task.completed;
        break;
      case 'pending':
        matchesFilter = !task.completed;
        break;
      case 'overdue':
        matchesFilter = (task.is_overdue ?? false) && !task.completed;
        break;
      default:
        matchesFilter = true;
    }

    // Apply search
    const matchesSearch =
      !searchQuery ||
      task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (task.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);

    return matchesFilter && matchesSearch;
  });

  const filterButtons: { key: FilterOption; label: string; count: number }[] = [
    {
      key: 'all',
      label: 'All Tasks',
      count: tasks.length,
    },
    {
      key: 'pending',
      label: 'Pending',
      count: tasks.filter((t) => !t.completed).length,
    },
    {
      key: 'completed',
      label: 'Completed',
      count: tasks.filter((t) => t.completed).length,
    },
    {
      key: 'overdue',
      label: 'Overdue',
      count: tasks.filter((t) => (t.is_overdue ?? false) && !t.completed).length,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-4 space-y-4">
        {/* Filter Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-5 h-5 text-gray-500 flex-shrink-0" />
          {filterButtons.map((filter) => (
            <button
              key={filter.key}
              onClick={() => setActiveFilter(filter.key)}
              className={cn(
                'px-4 py-2 rounded-lg font-medium text-sm transition-all',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                activeFilter === filter.key
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {filter.label}
              <span
                className={cn(
                  'ml-2 px-2 py-0.5 rounded-full text-xs font-semibold',
                  activeFilter === filter.key
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-200 text-gray-600'
                )}
              >
                {filter.count}
              </span>
            </button>
          ))}
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all"
          />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin mb-3" />
          <p className="text-gray-600">Loading tasks...</p>
        </div>
      )}

      {/* Task List */}
      {!isLoading && filteredTasks.length > 0 && (
        <div className="space-y-4">
          {filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onTaskUpdated={onTaskUpdated}
              onTaskDeleted={onTaskDeleted}
              onEditClick={onEditClick}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredTasks.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="text-center">
            <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
              <Filter className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No tasks found
            </h3>
            <p className="text-gray-600">
              {searchQuery
                ? `No tasks match "${searchQuery}"`
                : activeFilter === 'all'
                ? 'Create your first task to get started'
                : `No ${activeFilter} tasks`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
