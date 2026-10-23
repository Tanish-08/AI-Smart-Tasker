'use client';

import { useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Task } from '@/types/task';
import { regenerateInsult } from '@/lib/api';
import { cn } from '@/lib/utils';

interface DeadlineAlertProps {
  task: Task;
  onInsultRegenerated?: (newInsult: string) => void;
}

/**
 * DeadlineAlert component displays funny AI-generated insults for overdue tasks
 * Features a regenerate button to get new insults
 */
export default function DeadlineAlert({ task, onInsultRegenerated }: DeadlineAlertProps) {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [currentInsult, setCurrentInsult] = useState(task.ai_insult || '');
  const [error, setError] = useState<string | null>(null);

  const handleRegenerateInsult = async () => {
    setIsRegenerating(true);
    setError(null);

    try {
      const response = await regenerateInsult(task.id);
      setCurrentInsult(response.insult);
      if (onInsultRegenerated) {
        onInsultRegenerated(response.insult);
      }
    } catch (err) {
      console.error('Failed to regenerate insult:', err);
      setError('Failed to generate new insult. Please try again.');
    } finally {
      setIsRegenerating(false);
    }
  };

  if (!task.is_overdue && !task.ai_insult) {
    return null;
  }

  return (
    <div
      className={cn(
        'p-4 rounded-lg border-2 border-danger-300 bg-gradient-to-r from-danger-50 to-danger-100',
        'animate-fade-in'
      )}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        {/* Warning Icon with subtle bounce animation */}
        <div className="flex-shrink-0 mt-1">
          <AlertTriangle className="w-6 h-6 text-danger-600 animate-bounce-subtle" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Alert Title */}
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-sm font-bold text-danger-800 uppercase tracking-wide">
              Deadline Overdue!
            </h3>
          </div>

          {/* AI-Generated Insult - The Star of the Show! */}
          {currentInsult ? (
            <blockquote className="text-base font-medium text-danger-900 italic border-l-4 border-danger-400 pl-3 my-2">
              "{currentInsult}"
            </blockquote>
          ) : (
            <p className="text-sm text-danger-700">
              This task is overdue. Time to get it done!
            </p>
          )}

          {/* Error Message */}
          {error && (
            <p className="text-sm text-danger-600 mt-2">
              {error}
            </p>
          )}

          {/* Regenerate Button */}
          <button
            onClick={handleRegenerateInsult}
            disabled={isRegenerating}
            className={cn(
              'mt-3 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium',
              'text-danger-700 bg-white border-2 border-danger-300 rounded-lg',
              'hover:bg-danger-50 hover:border-danger-400 transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-danger-500 focus:ring-offset-2',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            aria-label="Generate a new insult"
          >
            <RefreshCw
              className={cn(
                'w-4 h-4',
                isRegenerating && 'animate-spin'
              )}
            />
            {isRegenerating ? 'Generating...' : 'Get Another Insult'}
          </button>
        </div>
      </div>

      {/* Humor Footer */}
      <div className="mt-3 pt-3 border-t border-danger-200">
        <p className="text-xs text-danger-600 text-center italic">
          Don't take it personally... but seriously, finish this task!
        </p>
      </div>
    </div>
  );
}
