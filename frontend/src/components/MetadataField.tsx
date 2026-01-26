import React from 'react';
import { useFormContext } from 'react-hook-form';

type Props = {
  label: string;
  name: string;
  readOnly?: boolean;
};

export const MetadataField: React.FC<Props> = ({ label, name, readOnly = false }) => {
  const { register } = useFormContext();
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-slate-600 w-32 flex-shrink-0">{label}</label>
      <input
        {...register(name)}
        readOnly={readOnly}
        className="flex-1 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-200"
        placeholder="-"
      />
    </div>
  );
};
