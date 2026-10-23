'use client';

import { useState } from 'react';
import { Calendar, CheckCircle2, Circle, Edit2, Trash2, Clock } from 'lucide-react';
import { Task } from '@/types/task';
import { toggleTaskCompletion, deleteTask } from '@/lib/api';
import {
  cn,
  formatDate,
  formatRelativeTime,
  getDeadlineStatus,
  truncateText,
  type DeadlineStatus,
} from '@/lib/utils';
import DeadlineAlert from './DeadlineAlert';
import SummaryGenerator from './SummaryGenerator';

const deadlineStatusLabels: Record<DeadlineStatus, string> = {
  completed: 'Completed',
  overdue: 'Overdue',
  urgent: 'Due soon',
  upcoming: 'Upcoming',
};

const deadlineStatusClasses: Record<DeadlineStatus, string> = {
  completed: 'bg-success-50 text-success-700 border-success-200',
  overdue: 'bg-danger-50 text-danger-700 border-danger-200',
  urgent: 'bg-warning-50 text-warning-700 border-warning-200',
  upcoming: 'bg-primary-50 text-primary-700 border-primary-200',
};

interface TaskCardProps {
  task: Task;
  onTaskUpdated: (task: Task) => void;
  onTaskDeleted: (taskId: number) => void;
  onEditClick: (task: Task) => void;
}

/**
 * TaskCard component displays a task with all its features:
 * - Task details (title, description, deadline)
 * - Completion status toggle
 * - AI-generated insults for overdue tasks
 * - AI summary generation and modification
 * - Edit and delete actions
 * - Visual deadline indicators
 */
export default function TaskCard({ task, onTaskUpdated, onTaskDeleted, onEditClick }: TaskCardProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [localTask, setLocalTask] = useState(task);
  const [showFullDescription, setShowFullDescription] = useState(false);

  const deadlineStatus = getDeadlineStatus(localTask);

  const handleToggleCompletion = async () => {
    setIsUpdating(true);
    try {
      const updatedTask = await toggleTaskCompletion(localTask.id, !localTask.completed);
      setLocalTask(updatedTask);
      onTaskUpdated(updatedTask);
    } catch (error) {
      console.error('Failed to toggle task completion:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this task?')) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteTask(localTask.id);
      onTaskDeleted(localTask.id);
    } catch (error) {
      console.error('Failed to delete task:', error);
      setIsDeleting(false);
    }
  };

  const handleSummaryUpdated = (summary: string) => {
    const updatedTask = { ...localTask, summary };
    setLocalTask(updatedTask);
    onTaskUpdated(updatedTask);
  };

  const handleInsultRegenerated = (newInsult: string) => {
    const updatedTask = { ...localTask, ai_insult: newInsult };
    setLocalTask(updatedTask);
    onTaskUpdated(updatedTask);
  };

  const descriptionText = localTask.description || 'No description provided';
  const shouldTruncate = descriptionText.length > 150;
  const displayDescription = showFullDescription
    ? descriptionText
    : truncateText(descriptionText, 150);

  return (
    <div
      className={cn(
        'bg-white rounded-lg shadow-md border-2 transition-all duration-200 hover:shadow-lg',
        localTask.completed ? 'border-success-200 bg-success-50/30' : 'border-gray-200',
        isDeleting && 'opacity-50 pointer-events-none'
      )}
    >
      <div className="p-5 space-y-4">
        {/* Header: Title and Actions */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            {/* Completion Checkbox */}
            <button
              onClick={handleToggleCompletion}
              disabled={isUpdating}
              className={cn(
                'flex-shrink-0 mt-1 transition-transform hover:scale-110',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-full',
                isUpdating && 'opacity-50 cursor-not-allowed'
              )}
              aria-label={localTask.completed ? 'Mark as incomplete' : 'Mark as complete'}
            >
              {localTask.completed ? (
                <CheckCircle2 className="w-6 h-6 text-success-600" />
              ) : (
                <Circle className="w-6 h-6 text-gray-400 hover:text-primary-600" />
              )}
            </button>

            {/* Title */}
            <div className="flex-1 min-w-0">
              <h3
                className={cn(
                  'text-lg font-semibold text-gray-900 break-words',
                  localTask.completed && 'line-through text-gray-500'
                )}
              >
                {localTask.title}
              </h3>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => onEditClick(localTask)}
              className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label="Edit task"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="p-2 text-danger-600 hover:bg-danger-50 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-danger-500 disabled:opacity-50"
              aria-label="Delete task"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Description */}
        <div className="pl-9">
          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
            {displayDescription}
          </p>
          {shouldTruncate && (
            <button
              onClick={() => setShowFullDescription(!showFullDescription)}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium mt-1 focus:outline-none focus:underline"
            >
              {showFullDescription ? 'Show less' : 'Read more'}
            </button>
          )}
        </div>

        {/* Deadline Status Badge */}
        <div className="pl-9">
          <div className="flex items-center gap-3 flex-wrap">
            <div
              className={cn(
                'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border-2',
                deadlineStatusClasses[deadlineStatus]
              )}
            >
              {localTask.completed ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <Clock className="w-4 h-4" />
              )}
              <span>{deadlineStatusLabels[deadlineStatus]}</span>
            </div>

            {/* Deadline Date */}
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Calendar className="w-4 h-4" />
              <span>
                <span className="font-medium">{formatDate(localTask.deadline)}</span>
                <span className="text-gray-500 ml-2">
                  ({formatRelativeTime(localTask.deadline)})
                </span>
              </span>
            </div>
          </div>
        </div>

        {/* AI-Generated Insult for Overdue Tasks */}
        {(localTask.is_overdue ?? false) && !localTask.completed && (
          <div className="pl-9">
            <DeadlineAlert task={localTask} onInsultRegenerated={handleInsultRegenerated} />
          </div>
        )}

        {/* AI Summary Section */}
        {!localTask.completed && (
          <div className="pl-9 pt-2 border-t border-gray-100">
            <SummaryGenerator task={localTask} onSummaryUpdated={handleSummaryUpdated} />
          </div>
        )}

        {/* Task Metadata Footer */}
        <div className="pl-9 pt-2 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Created {formatRelativeTime(localTask.created_at)}</span>
            {localTask.updated_at !== localTask.created_at && (
              <span>Updated {formatRelativeTime(localTask.updated_at)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
