import React, { useState } from 'react';

export default function Playground() {
  const [file, setFile] = useState(null);
  const [mod, setMod] = useState('image');
  const [result, setResult] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!file) return;
    setLoading(true);
    setResult(null);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('options', JSON.stringify({ check_provenance: true, check_watermarks: true, check_visual: true, check_audio: true }));
    const res = await fetch(`/v1/${mod}s:analyze`, { method: 'POST', body: fd });
    const data = await res.json();
    setJobId(data.job_id);
    setTimeout(async () => {
      const r = await fetch(`/v1/jobs/${data.job_id}`);
      const j = await r.json();
      setResult(j);
      setLoading(false);
    }, 1000);
  }

  return (
    <div>
      <h2 className='text-2xl font-bold mb-4'>Playground</h2>
      <div className='card'>
        <div className='flex items-center gap-3'>
          <select className='border rounded-lg px-3 py-2' value={mod} onChange={e=>setMod(e.target.value)}>
            <option value='image'>Image</option>
            <option value='audio'>Audio</option>
            <option value='video'>Video</option>
          </select>
          <input type='file' onChange={e => setFile(e.target.files?.[0])} />
          <button className='btn' onClick={submit} disabled={loading || !file}>{loading ? 'Analyzing...' : 'Analyze'}</button>
        </div>
        {jobId && <div className='mt-2 text-sm text-slate-600'>Job: {jobId}</div>}
      </div>

      {result && (
        <div className='card mt-4'>
          <h3 className='font-semibold mb-2'>Result</h3>
          <pre className='bg-slate-900 text-slate-100 p-3 rounded-xl overflow-auto text-sm'>
{JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
