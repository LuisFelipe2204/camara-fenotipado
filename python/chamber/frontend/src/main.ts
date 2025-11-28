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

const FETCH_INTERVAL = 2000;
setInterval(async () => {
  const res = await fetch("/api/dashboard");
  // const res = {
  //   ok: true,
  //   json: () => ({
  //     temp: Math.random() * 50,
  //     "white-light": Math.random() * 1000,
  //     "ir-light": Math.random() * 1000,
  //     "uv-light": Math.random() * 14,
  //     hum: Math.random() * 100,
  //     angle: Math.random() * 300,
  //     progress: Math.random() * 100,
  //     running: Math.random() > 0.5 ? 1 : 0,
  //   }),
  // };
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

function getPercentage(value: number, min: number, max: number) {
  return (value - min) / (max - min);
}

function applyPercentage(percentage: number, min: number, max: number) {
  return min + (max - min) * percentage;
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
