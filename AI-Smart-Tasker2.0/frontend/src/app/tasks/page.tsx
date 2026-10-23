'use client';

import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { Task } from '@/types/task';
import { getTasks } from '@/lib/api';
import { cn } from '@/lib/utils';
import TaskList from '@/components/TaskList';
import TaskForm from '@/components/TaskForm';
import Modal from '@/components/Modal';

/**
 * Tasks page with full task list, filtering, and management
 */
export default function TasksPage() {
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

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">All Tasks</h1>
          <p className="text-gray-600 mt-1">
            Manage your tasks with filtering, search, and AI-powered features
          </p>
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

      {/* Task List with Filtering */}
      <TaskList
        tasks={tasks}
        onTaskUpdated={handleTaskUpdated}
        onTaskDeleted={handleTaskDeleted}
        onEditClick={setEditingTask}
        isLoading={isLoading}
      />

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
