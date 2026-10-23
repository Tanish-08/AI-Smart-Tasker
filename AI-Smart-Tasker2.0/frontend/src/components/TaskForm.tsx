'use client';

import { useState } from 'react';
import { Save, X } from 'lucide-react';
import { Task, TaskCreate, TaskUpdate, TaskPriority } from '@/types/task';
import { createTask, updateTask } from '@/lib/api';
import { isoToLocalDatetime, localDatetimeToISO, cn } from '@/lib/utils';

interface TaskFormProps {
  task?: Task;
  onSuccess: (task: Task) => void;
  onCancel: () => void;
}

/**
 * TaskForm component for creating and editing tasks
 * Features form validation, priority selection, and responsive design
 */
export default function TaskForm({ task, onSuccess, onCancel }: TaskFormProps) {
  const [title, setTitle] = useState(task?.title || '');
  const [description, setDescription] = useState(task?.description || '');
  const [deadline, setDeadline] = useState(
    task?.deadline ? isoToLocalDatetime(task.deadline) : ''
  );
  const [priority, setPriority] = useState<TaskPriority>(task?.priority || TaskPriority.MEDIUM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEditMode = !!task;

  // Set minimum datetime to current time
  const getMinDatetime = () => {
    const now = new Date();
    return isoToLocalDatetime(now.toISOString());
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = 'Title is required';
    } else if (title.length > 200) {
      newErrors.title = 'Title must be less than 200 characters';
    }

    if (description.length > 2000) {
      newErrors.description = 'Description must be less than 2000 characters';
    }

    if (!deadline) {
      newErrors.deadline = 'Deadline is required';
    } else {
      const deadlineDate = new Date(deadline);
      const now = new Date();
      if (deadlineDate <= now && !isEditMode) {
        newErrors.deadline = 'Deadline must be in the future';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      if (isEditMode) {
        const updateData: TaskUpdate = {
          title: title.trim(),
          description: description.trim() || undefined,
          deadline: localDatetimeToISO(deadline),
          priority,
        };
        const updatedTask = await updateTask(task.id, updateData);
        onSuccess(updatedTask);
      } else {
        const createData: TaskCreate = {
          title: title.trim(),
          description: description.trim() || undefined,
          deadline: localDatetimeToISO(deadline),
          priority,
        };
        const newTask = await createTask(createData);
        onSuccess(newTask);
      }
    } catch (error) {
      console.error('Failed to save task:', error);
      setErrors({ submit: 'Failed to save task. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Title Field */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
          Task Title <span className="text-danger-600">*</span>
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={cn(
            'w-full px-4 py-2.5 border-2 rounded-lg transition-all',
            'focus:outline-none focus:ring-2 focus:ring-primary-200',
            errors.title
              ? 'border-danger-300 focus:border-danger-500'
              : 'border-gray-300 focus:border-primary-500'
          )}
          placeholder="Enter task title..."
          maxLength={200}
          aria-invalid={!!errors.title}
          aria-describedby={errors.title ? 'title-error' : undefined}
        />
        {errors.title && (
          <p id="title-error" className="mt-1 text-sm text-danger-600">
            {errors.title}
          </p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          {title.length}/200 characters
        </p>
      </div>

      {/* Description Field */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={cn(
            'w-full px-4 py-2.5 border-2 rounded-lg transition-all resize-none',
            'focus:outline-none focus:ring-2 focus:ring-primary-200',
            errors.description
              ? 'border-danger-300 focus:border-danger-500'
              : 'border-gray-300 focus:border-primary-500'
          )}
          rows={4}
          placeholder="Add task details, notes, or requirements..."
          maxLength={2000}
          aria-invalid={!!errors.description}
          aria-describedby={errors.description ? 'description-error' : undefined}
        />
        {errors.description && (
          <p id="description-error" className="mt-1 text-sm text-danger-600">
            {errors.description}
          </p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          {description.length}/2000 characters
        </p>
      </div>

      {/* Deadline Field */}
      <div>
        <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-2">
          Deadline <span className="text-danger-600">*</span>
        </label>
        <input
          type="datetime-local"
          id="deadline"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
          min={!isEditMode ? getMinDatetime() : undefined}
          className={cn(
            'w-full px-4 py-2.5 border-2 rounded-lg transition-all',
            'focus:outline-none focus:ring-2 focus:ring-primary-200',
            errors.deadline
              ? 'border-danger-300 focus:border-danger-500'
              : 'border-gray-300 focus:border-primary-500'
          )}
          aria-invalid={!!errors.deadline}
          aria-describedby={errors.deadline ? 'deadline-error' : undefined}
        />
        {errors.deadline && (
          <p id="deadline-error" className="mt-1 text-sm text-danger-600">
            {errors.deadline}
          </p>
        )}
      </div>

      {/* Priority Field */}
      <div>
        <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
          Priority
        </label>
        <select
          id="priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value as TaskPriority)}
          className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all"
        >
          <option value={TaskPriority.LOW}>Low</option>
          <option value={TaskPriority.MEDIUM}>Medium</option>
          <option value={TaskPriority.HIGH}>High</option>
        </select>
      </div>

      {/* Submit Error */}
      {errors.submit && (
        <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg">
          <p className="text-sm text-danger-700">{errors.submit}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className={cn(
            'flex-1 inline-flex items-center justify-center gap-2 px-4 py-3',
            'text-white bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg font-medium',
            'hover:from-primary-700 hover:to-primary-800 transition-all shadow-md',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <Save className="w-5 h-5" />
          {isSubmitting
            ? isEditMode
              ? 'Updating...'
              : 'Creating...'
            : isEditMode
            ? 'Update Task'
            : 'Create Task'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-4 py-3 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium disabled:opacity-50"
        >
          <X className="w-5 h-5 inline mr-2" />
          Cancel
        </button>
      </div>
    </form>
  );
}
