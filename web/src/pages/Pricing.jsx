import React from "react";

export default function Pricing() {
  async function startPro() {
    const res = await fetch("/billing/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}) // uses STRIPE_PRICE_PRO_MONTH if set
    });
    if (!res.ok) {
      const t = await res.text();
      alert("Billing not configured: " + t);
      return;
    }
    const { checkout_url } = await res.json();
    window.location = checkout_url;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Pricing</h2>
      <div className="grid md:grid-cols-3 gap-6">
        <div className="card">
          <div className="text-xl font-bold">Starter</div>
          <div className="text-4xl font-extrabold mt-2">$0</div>
          <ul className="mt-3 text-slate-600 list-disc pl-6">
            <li>100 analyses / month</li>
            <li>Shared workers</li>
            <li>Email support</li>
          </ul>
          <button className="btn mt-4" onClick={() => (window.location = "/register")}>Get started</button>
        </div>
        <div className="card border-2 border-brand">
          <div className="text-xl font-bold">Pro</div>
          <div className="text-4xl font-extrabold mt-2">$99</div>
          <ul className="mt-3 text-slate-600 list-disc pl-6">
            <li>20k analyses / month</li>
            <li>Priority processing</li>
            <li>Webhook callbacks</li>
          </ul>
          <button className="btn mt-4" onClick={startPro}>Start Pro</button>
        </div>
        <div className="card">
          <div className="text-xl font-bold">Enterprise</div>
          <div className="text-4xl font-extrabold mt-2">Custom</div>
          <ul className="mt-3 text-slate-600 list-disc pl-6">
            <li>SLA & SSO</li>
            <li>Dedicated tenancy</li>
            <li>Custom thresholds</li>
          </ul>
          <button className="btn mt-4" onClick={() => alert('We’ll reach out!')}>Contact sales</button>
        </div>
      </div>
    </div>
  );
}
