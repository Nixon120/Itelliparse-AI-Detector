import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [me, setMe] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      const r = await fetch('/me');
      if (!r.ok) return nav('/login');
      const j = await r.json();
      setMe(j);
    })();
  }, []);

  return (
    <div>
      <h2 className='text-2xl font-bold mb-4'>Dashboard</h2>
      {!me ? <div className="card">Loading...</div> : (
        <>
          <div className='grid md:grid-cols-3 gap-4'>
            <div className='card'><div className='text-sm text-slate-500'>API Key</div><div className='text-xl font-mono mt-2'>{me.api_key}</div></div>
            <div className='card'><div className='text-sm text-slate-500'>Requests (today)</div><div className='text-3xl font-bold mt-2'>42</div></div>
            <div className='card'><div className='text-sm text-slate-500'>Success rate</div><div className='text-3xl font-bold mt-2'>99.2%</div></div>
          </div>
          <div className='card mt-4'>
            <h3 className='font-semibold'>Model Metrics</h3>
            <Metrics />
          </div>
        </>
      )}
    </div>
  );
}

function Metrics(){
  const [m, setM] = useState(null);
  useEffect(() => { (async () => { const r = await fetch('/v1/metrics'); setM(await r.json()); })(); }, []);
  if(!m) return <div className="text-slate-500">Fetching metrics…</div>;
  return (
    <pre className='bg-slate-900 text-slate-100 p-3 rounded-xl overflow-auto text-sm'>{JSON.stringify(m, null, 2)}</pre>
  );
}
