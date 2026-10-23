// Helper functions used across the frontend components
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Task } from '@/types/task';

/** Merge Tailwind class names safely */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** 1234567 -> "1,234,567" */
export function formatNumber(value: number | undefined | null): string {
  return (value ?? 0).toLocaleString('en-US');
}

/** Hours -> "2h 30m" or "1d 4h" */
export function formatDuration(hours: number | undefined | null): string {
  const h = Math.abs(hours ?? 0);
  if (h < 1) return `${Math.round(h * 60)}m`;
  if (h < 24) {
    const mins = Math.round((h - Math.floor(h)) * 60);
    return mins ? `${Math.floor(h)}h ${mins}m` : `${Math.floor(h)}h`;
  }
  const days = Math.floor(h / 24);
  const rem = Math.round(h - days * 24);
  return rem ? `${days}d ${rem}h` : `${days}d`;
}

/** Accepts (completed, total) or an array of tasks. Returns a whole-number percentage. */
export function calculateCompletionRate(a: number | Task[], b?: number): number {
  let completed: number;
  let total: number;
  if (Array.isArray(a)) {
    total = a.length;
    completed = a.filter((t) => t.completed).length;
  } else {
    completed = a;
    total = b ?? 0;
  }
  return total > 0 ? Math.round((completed / total) * 100) : 0;
}

/** "Dec 31, 2026, 6:00 PM" */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

/** "in 2 days", "3 hours ago" */
export function formatRelativeTime(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  const diffSec = Math.round((d.getTime() - Date.now()) / 1000);
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ];
  for (const [unit, secs] of units) {
    if (Math.abs(diffSec) >= secs) return rtf.format(Math.round(diffSec / secs), unit);
  }
  return rtf.format(diffSec, 'second');
}

export type DeadlineStatus = 'completed' | 'overdue' | 'urgent' | 'upcoming';

/** Pass a deadline string (and completed flag) or a task object */
export function getDeadlineStatus(
  deadlineOrTask: string | Pick<Task, 'deadline' | 'completed'>,
  completed = false
): DeadlineStatus {
  const deadline = typeof deadlineOrTask === 'string' ? deadlineOrTask : deadlineOrTask.deadline;
  const isDone = typeof deadlineOrTask === 'string' ? completed : deadlineOrTask.completed;

  if (isDone) return 'completed';
  const msLeft = new Date(deadline).getTime() - Date.now();
  if (msLeft < 0) return 'overdue';
  if (msLeft < 24 * 60 * 60 * 1000) return 'urgent';
  return 'upcoming';
}

export function truncateText(text: string | undefined | null, maxLength = 100): string {
  if (!text) return '';
  return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}...` : text;
}

/** ISO string -> value for <input type="datetime-local"> ("2026-12-31T18:00") */
export function isoToLocalDatetime(iso: string | undefined | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Value from <input type="datetime-local"> -> ISO string */
export function localDatetimeToISO(local: string): string {
  const d = new Date(local);
  return isNaN(d.getTime()) ? '' : d.toISOString();
}