'use client';

import EntryForm from '@/components/entries/entry-form';

export default function NewEntryPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Entry</h1>
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        <EntryForm />
      </div>
    </div>
  );
}
