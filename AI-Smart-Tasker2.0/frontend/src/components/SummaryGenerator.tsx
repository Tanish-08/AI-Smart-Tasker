'use client';

import { useState, useRef, useEffect } from 'react';
import { Sparkles, Edit3, Wand2, Save, X, ChevronDown } from 'lucide-react';
import { Task } from '@/types/task';
import { generateSummary, modifySummary, updateSummaryManually } from '@/lib/api';
import { cn } from '@/lib/utils';
import Modal from './Modal';

interface SummaryGeneratorProps {
  task: Task;
  onSummaryUpdated: (summary: string) => void;
}

type EditMode = 'none' | 'manual' | 'ai';

/**
 * SummaryGenerator component handles AI-powered task summary generation and editing
 * Features:
 * - Generate AI summary button
 * - Modify dropdown with Manual Edit and AI Edit options
 * - Modal for AI-powered modifications
 */
export default function SummaryGenerator({ task, onSummaryUpdated }: SummaryGeneratorProps) {
  const [summary, setSummary] = useState(task.summary || '');
  const [isGenerating, setIsGenerating] = useState(false);
  const [editMode, setEditMode] = useState<EditMode>('none');
  const [manualEditValue, setManualEditValue] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [isModifying, setIsModifying] = useState(false);
  const [showModifyMenu, setShowModifyMenu] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const modifyMenuRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Close modify menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modifyMenuRef.current && !modifyMenuRef.current.contains(event.target as Node)) {
        setShowModifyMenu(false);
      }
    };

    if (showModifyMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showModifyMenu]);

  // Focus textarea when manual edit mode is activated
  useEffect(() => {
    if (editMode === 'manual' && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [editMode]);

  const handleGenerateSummary = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await generateSummary(task.id);
      setSummary(response.summary);
      onSummaryUpdated(response.summary);
    } catch (err) {
      console.error('Failed to generate summary:', err);
      setError('Failed to generate summary. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleManualEdit = () => {
    setManualEditValue(summary);
    setEditMode('manual');
    setShowModifyMenu(false);
  };

  const handleSaveManualEdit = async () => {
    setIsModifying(true);
    setError(null);

    try {
      await updateSummaryManually(task.id, manualEditValue);
      setSummary(manualEditValue);
      onSummaryUpdated(manualEditValue);
      setEditMode('none');
    } catch (err) {
      console.error('Failed to save manual edit:', err);
      setError('Failed to save changes. Please try again.');
    } finally {
      setIsModifying(false);
    }
  };

  const handleCancelManualEdit = () => {
    setEditMode('none');
    setManualEditValue('');
    setError(null);
  };

  const handleAIEdit = () => {
    setEditMode('ai');
    setShowModifyMenu(false);
    setAiPrompt('');
  };

  const handleSubmitAIEdit = async () => {
    if (!aiPrompt.trim()) {
      setError('Please enter a modification prompt');
      return;
    }

    setIsModifying(true);
    setError(null);

    try {
      const response = await modifySummary(task.id, aiPrompt);
      setSummary(response.summary);
      onSummaryUpdated(response.summary);
      setEditMode('none');
      setAiPrompt('');
    } catch (err) {
      console.error('Failed to modify summary with AI:', err);
      setError('Failed to modify summary. Please try again.');
    } finally {
      setIsModifying(false);
    }
  };

  const handleCloseAIModal = () => {
    setEditMode('none');
    setAiPrompt('');
    setError(null);
  };

  return (
    <div className="space-y-4">
      {/* Generate Summary Button (shown when no summary exists) */}
      {!summary && (
        <button
          onClick={handleGenerateSummary}
          disabled={isGenerating}
          className={cn(
            'w-full inline-flex items-center justify-center gap-2 px-4 py-3',
            'text-white bg-gradient-to-r from-primary-600 to-primary-700',
            'rounded-lg font-medium shadow-md',
            'hover:from-primary-700 hover:to-primary-800 transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <Sparkles className={cn('w-5 h-5', isGenerating && 'animate-spin')} />
          {isGenerating ? 'Generating AI Summary...' : 'Generate AI Summary'}
        </button>
      )}

      {/* Summary Display */}
      {summary && editMode === 'none' && (
        <div className="space-y-3">
          <div className="p-4 bg-primary-50 border border-primary-200 rounded-lg">
            <div className="flex items-start gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-primary-600 mt-0.5 flex-shrink-0" />
              <h4 className="text-sm font-semibold text-primary-900">AI Summary</h4>
            </div>
            <p className="text-gray-800 leading-relaxed">{summary}</p>
          </div>

          {/* Modify Button with Dropdown */}
          <div className="relative" ref={modifyMenuRef}>
            <button
              onClick={() => setShowModifyMenu(!showModifyMenu)}
              className={cn(
                'w-full inline-flex items-center justify-center gap-2 px-4 py-2',
                'text-primary-700 bg-white border-2 border-primary-300 rounded-lg',
                'hover:bg-primary-50 hover:border-primary-400 transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2'
              )}
            >
              <Wand2 className="w-4 h-4" />
              Modify Summary
              <ChevronDown className="w-4 h-4 ml-auto" />
            </button>

            {/* Dropdown Menu */}
            {showModifyMenu && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10 animate-fade-in">
                <button
                  onClick={handleManualEdit}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-100"
                >
                  <Edit3 className="w-4 h-4 text-gray-600" />
                  <div>
                    <div className="font-medium text-gray-900">Manual Edit</div>
                    <div className="text-xs text-gray-500">Edit the summary directly</div>
                  </div>
                </button>
                <button
                  onClick={handleAIEdit}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                >
                  <Wand2 className="w-4 h-4 text-primary-600" />
                  <div>
                    <div className="font-medium text-gray-900">AI Edit</div>
                    <div className="text-xs text-gray-500">Modify using natural language</div>
                  </div>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Edit Mode */}
      {editMode === 'manual' && (
        <div className="space-y-3">
          <textarea
            ref={textareaRef}
            value={manualEditValue}
            onChange={(e) => setManualEditValue(e.target.value)}
            className="w-full p-4 border-2 border-primary-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all resize-none"
            rows={4}
            placeholder="Edit your summary..."
          />
          <div className="flex gap-2">
            <button
              onClick={handleSaveManualEdit}
              disabled={isModifying || !manualEditValue.trim()}
              className={cn(
                'flex-1 inline-flex items-center justify-center gap-2 px-4 py-2',
                'text-white bg-success-600 rounded-lg font-medium',
                'hover:bg-success-700 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-success-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <Save className="w-4 h-4" />
              {isModifying ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={handleCancelManualEdit}
              disabled={isModifying}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <X className="w-4 h-4" />
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* AI Edit Modal */}
      <Modal
        isOpen={editMode === 'ai'}
        onClose={handleCloseAIModal}
        title="AI-Powered Summary Modification"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Describe how you'd like to modify the summary. Be specific about what changes you want.
          </p>

          <div>
            <label htmlFor="ai-prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Modification Prompt
            </label>
            <textarea
              id="ai-prompt"
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all resize-none"
              rows={4}
              placeholder='Example: "Make it more concise" or "Add technical details" or "Make it sound more professional"'
            />
          </div>

          {error && (
            <div className="p-3 bg-danger-50 border border-danger-200 rounded-lg">
              <p className="text-sm text-danger-700">{error}</p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              onClick={handleSubmitAIEdit}
              disabled={isModifying || !aiPrompt.trim()}
              className={cn(
                'flex-1 inline-flex items-center justify-center gap-2 px-4 py-3',
                'text-white bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg font-medium',
                'hover:from-primary-700 hover:to-primary-800 transition-all',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <Wand2 className={cn('w-5 h-5', isModifying && 'animate-spin')} />
              {isModifying ? 'Modifying...' : 'Modify with AI'}
            </button>
            <button
              onClick={handleCloseAIModal}
              disabled={isModifying}
              className="px-4 py-3 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      </Modal>

      {/* Error Display */}
      {error && editMode !== 'ai' && (
        <div className="p-3 bg-danger-50 border border-danger-200 rounded-lg">
          <p className="text-sm text-danger-700">{error}</p>
        </div>
      )}
    </div>
  );
}
