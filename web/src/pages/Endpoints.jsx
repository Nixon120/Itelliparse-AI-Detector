import React from 'react';

const Block = ({title, children}) => (
  <div className='card'>
    <h3 className='font-semibold'>{title}</h3>
    <div className='mt-2 text-sm text-slate-700'>{children}</div>
  </div>
);

export default function Endpoints() {
  return (
    <div>
      <h2 className='text-2xl font-bold mb-4'>Endpoints</h2>
      <Block title='POST /v1/images:analyze'>
        <pre className='bg-slate-900 text-slate-100 p-3 rounded-xl overflow-auto text-sm'>
curl -F "file=@sample.jpg" -F 'options={{"check_provenance":true,"check_watermarks":true}}' http://localhost:8000/v1/images:analyze
        </pre>
      </Block>
      <Block title='POST /v1/audio:analyze'>
        <pre className='bg-slate-900 text-slate-100 p-3 rounded-xl overflow-auto text-sm'>
curl -F "file=@sample.wav" -F 'options={{"check_audio":true}}' http://localhost:8000/v1/audio:analyze
        </pre>
      </Block>
      <Block title='POST /v1/videos:analyze'>
        <pre className='bg-slate-900 text-slate-100 p-3 rounded-xl overflow-auto text-sm'>
curl -F "file=@sample.mp4" -F 'options={{"check_visual":true,"check_audio":true}}' http://localhost:8000/v1/videos:analyze
        </pre>
      </Block>
      <Block title='GET /v1/jobs/{job_id}'>
        <pre className='bg-slate-900 text-slate-100 p-3 rounded-xl overflow-auto text-sm'>
curl http://localhost:8000/v1/jobs/job_123
        </pre>
      </Block>
    </div>
  );
}
