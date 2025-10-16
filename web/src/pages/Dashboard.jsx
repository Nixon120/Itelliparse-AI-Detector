import React from 'react';

export default function Dashboard() {
  return (
    <div>
      <h2 className='text-2xl font-bold mb-4'>Dashboard</h2>
      <div className='grid md:grid-cols-3 gap-4'>
        <div className='card'><div className='text-sm text-slate-500'>Requests (today)</div><div className='text-3xl font-bold mt-2'>42</div></div>
        <div className='card'><div className='text-sm text-slate-500'>Success rate</div><div className='text-3xl font-bold mt-2'>99.2%</div></div>
        <div className='card'><div className='text-sm text-slate-500'>Avg latency</div><div className='text-3xl font-bold mt-2'>1.2s</div></div>
      </div>
      <div className='card mt-4'>
        <h3 className='font-semibold'>Recent Jobs</h3>
        <ul className='mt-2 list-disc pl-6 text-slate-600'>
          <li>job_3fd9e2a1 — image — completed</li>
          <li>job_1a92bb53 — audio — completed</li>
          <li>job_d76d220e — video — completed</li>
        </ul>
      </div>
    </div>
  );
}
