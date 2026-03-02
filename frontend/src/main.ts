import "./main.css";
import "./styles/dashboard.css";
import "./styles/header.css";
import "./styles/background.css";

import "./components/widget.css";
import "./components/live-camera";
import "./components/widget-thermo";
import "./components/widget-bulb";
import "./components/widget-gauge";
import "./components/widget-value";
import "./components/widget-bar";
import "./components/widget-button";

import "./controls";
import "./results";
import "./popup";

const FETCH_INTERVAL = 500;
setInterval(async () => {
  const res = await fetch("/api/dashboard");
  if (!res.ok) {
    console.error("Error fetching dashboard data.", res);
    return;
  }

  const data = await res.json();
  Object.entries(data).forEach(([key, value]) => {
    const widget = document.getElementById(key);
    if (!widget) {
      console.warn("Received key with no available widget", [key, value]);
      return;
    }

    widget.setAttribute("value", String(value));
  });
}, FETCH_INTERVAL);

function clamp(value: number, min: number, max: number) {
  return Math.max(Math.min(value, max), min);
}

function getPercentage(value: number, min: number, max: number) {
  return (value - min) / (max - min);
}

function applyPercentage(percentage: number, min: number, max: number) {
  return clamp(min + (max - min) * percentage, min, max);
}

async function poll(src: string, maxAttempts = 10) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(src, { headers: { "Content-Type": "application/json" } });
      if (res.status !== 200) continue;

      return await res.json();
    } catch (err) {
      console.error("Error polling", err);
    } finally {
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }

  return null;
}

export { applyPercentage, getPercentage, poll };
