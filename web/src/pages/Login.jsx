import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState('');
  const nav = useNavigate();

  async function submit(e){
    e.preventDefault();
    setErr('');
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if(res.ok){
      const j = await res.json();
      localStorage.setItem('ip_user', JSON.stringify(j));
      nav('/dashboard');
    } else {
      setErr('Invalid email or password');
    }
  }

  return (
    <div className="container p-8 max-w-md">
      <h2 className="text-2xl font-bold mb-4">Sign in</h2>
      <form onSubmit={submit} className="card">
        <input className="border rounded-lg px-3 py-2 w-full mb-2" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="border rounded-lg px-3 py-2 w-full mb-2" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        {err && <div className="text-red-600 text-sm mb-2">{err}</div>}
        <button className="btn">Sign in</button>
      </form>
    </div>
  );
}
