import React, { useState } from 'react';

export default function Settings() {
  const [webhook, setWebhook] = useState('');
  const [apiKey] = useState('sk-test_********');

  return (
    <div>
      <h2 className='text-2xl font-bold mb-4'>Settings</h2>
      <div className='card'>
        <div className='mb-3'>
          <label className='block text-sm font-medium'>API Key</label>
          <input readOnly value={apiKey} className='mt-1 border rounded-lg px-3 py-2 w-full' />
          <p className='text-xs text-slate-500 mt-1'>Use this key in Authorization headers (Bearer).</p>
        </div>
        <div className='mb-3'>
          <label className='block text-sm font-medium'>Webhook URL</label>
          <input value={webhook} onChange={e=>setWebhook(e.target.value)} className='mt-1 border rounded-lg px-3 py-2 w-full' placeholder='https://yourapp.example.com/webhook' />
        </div>
        <button className='btn'>Save</button>
      </div>
    </div>
  );
}
