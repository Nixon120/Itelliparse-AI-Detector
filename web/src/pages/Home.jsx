import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className='container p-8'>
      <header className='text-center mt-16'>
        <h1 className='text-5xl font-extrabold tracking-tight'>Detect AI media with confidence</h1>
        <p className='mt-4 text-lg text-slate-600'>
          intelliparse scores images, audio, and video for AI-generation, deepfakes, and voice cloning—privacy-first.
        </p>
        <div className='mt-8 flex gap-4 justify-center'>
          <Link to='/playground' className='btn'>Try the Playground</Link>
          <Link to='/pricing' className='btn' style={{background:'#111'}}>See Pricing</Link>
        </div>
      </header>
      <section className='grid md:grid-cols-3 gap-6 mt-16'>
        <div className='card'><h3 className='font-semibold text-lg'>Multi‑signal</h3><p className='text-slate-600 mt-2'>Provenance, watermarks, visual, audio, and consent-based identity checks.</p></div>
        <div className='card'><h3 className='font-semibold text-lg'>Simple API</h3><p className='text-slate-600 mt-2'>Upload media, get a calibrated score and explanations.</p></div>
        <div className='card'><h3 className='font-semibold text-lg'>Privacy-first</h3><p className='text-slate-600 mt-2'>Opt-in watchlists only. Short retention. Clear limitations.</p></div>
      </section>
    </div>
  );
}
