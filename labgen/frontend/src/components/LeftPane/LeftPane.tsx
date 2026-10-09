import { useState } from 'react';
import { cn } from '../../lib/utils';
import { Send, Loader2 } from 'lucide-react';
import { FormData } from '../../types/pipeline';
import { AccordionSection } from './AccordionSection';
import { AdminMetadata } from './AdminMetadata';
import { TechnicalConstraints } from './TechnicalConstraints';

interface LeftPaneProps {
  formData: FormData;
  onChange: (field: keyof FormData, value: any) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  validationErrors?: Partial<Record<keyof FormData, string>>;
}

const INITIAL_FORM_DATA: FormData = {
  studentName: '',
  rollNumber: '',
  section: 'A',
  group: 1,
  experimentName: '',
  experimentNumber: 2,
  circuitDescription: '',
  boundaryConditions: {},
  cadParameters: {},
};

export function LeftPane({ 
  formData, 
  onChange, 
  onGenerate, 
  isGenerating, 
  validationErrors 
}: LeftPaneProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate();
  };

  return (
    <div className="w-96 flex-shrink-0 bg-slate-900/50 border-r border-slate-700 flex flex-col h-full">
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-lg font-semibold text-white">Inputs & Parameters</h2>
        <p className="text-xs text-slate-500 mt-1">Configure generation pipeline</p>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 space-y-4">
        <AccordionSection 
          title="Administrative Metadata" 
          description="Student and experiment identification"
          defaultOpen={false}
        >
          <AdminMetadata 
            formData={formData} 
            onChange={onChange}
            errors={validationErrors}
          />
        </AccordionSection>

        <AccordionSection 
          title="Experiment Configuration" 
          description="Core experiment parameters"
          defaultOpen={true}
        >
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="block text-xs font-medium text-slate-300">Experiment Name</label>
              <input
                type="text"
                value={formData.experimentName}
                onChange={(e) => onChange('experimentName', e.target.value)}
                placeholder="TRIAC Characteristics Analysis"
                className={cn(
                  'w-full px-3 py-2 bg-slate-900 border rounded-lg text-white placeholder-slate-500',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent',
                  'transition-colors',
                  validationErrors?.experimentName && 'border-red-500/50 focus:ring-red-500/50'
                )}
              />
              {validationErrors?.experimentName && (
                <p className="text-xs text-red-400">{validationErrors.experimentName}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-medium text-slate-300">Experiment Number</label>
              <input
                type="number"
                value={formData.experimentNumber}
                onChange={(e) => onChange('experimentNumber', parseInt(e.target.value) || 2)}
                min={1}
                max={99}
                className={cn(
                  'w-full px-3 py-2 bg-slate-900 border rounded-lg text-white placeholder-slate-500',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent',
                  'transition-colors'
                )}
              />
            </div>
          </div>
        </AccordionSection>

        <AccordionSection 
          title="Technical Constraints" 
          description="Circuit description, boundary conditions, CAD parameters"
          defaultOpen={true}
        >
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="block text-xs font-medium text-slate-300">Circuit Description</label>
              <textarea
                value={formData.circuitDescription}
                onChange={(e) => onChange('circuitDescription', e.target.value)}
                placeholder="Describe the circuit topology, components, and connections..."
                rows={4}
                className={cn(
                  'w-full px-3 py-2 bg-slate-900 border rounded-lg text-white placeholder-slate-500 resize-y min-h-[100px]',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent',
                  'transition-colors font-mono text-sm',
                  validationErrors?.circuitDescription && 'border-red-500/50 focus:ring-red-500/50'
                )}
              />
              {validationErrors?.circuitDescription && (
                <p className="text-xs text-red-400">{validationErrors.circuitDescription}</p>
              )}
            </div>

            <TechnicalConstraints 
              formData={formData} 
              onChange={onChange}
            />
          </div>
        </AccordionSection>
      </form>

      {/* Generate Button - Fixed at bottom */}
      <div className="p-4 border-t border-slate-700 bg-slate-900/30">
        <button
          type="button"
          onClick={onGenerate}
          disabled={isGenerating || !formData.experimentName || !formData.circuitDescription}
          className={cn(
            'w-full px-4 py-3 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2',
            'focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2 focus:ring-offset-slate-900',
            isGenerating 
              ? 'bg-blue-500/20 text-blue-400 cursor-not-allowed' 
              : (!formData.experimentName || !formData.circuitDescription)
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/25'
          )}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              GENERATING...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              INITIATE GENERATION
            </>
          )}
        </button>
        <p className="text-xs text-slate-500 text-center mt-2">
          Requires: Experiment Name + Circuit Description
        </p>
      </div>
    </div>
  );
}