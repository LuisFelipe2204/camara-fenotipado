const Variables = {
  temp: document.getElementById("temp"),
  hum: document.getElementById("hum"),
  white_lux: document.getElementById("white_lux"),
  ir_lux: document.getElementById("ir_lux"),
  uv_lux: document.getElementById("uv_lux"),
  running: document.getElementById("running"),
};

const Limits = {
  temp: [-10, 50],
  hum: [0, 100],
  white_lux: [0, 1000],
  ir_lux: [0, 1000],
  uv_lux: [0, 16],
  running: [0, 1],
};

const loop = async () => {
  const res = await fetch("/api/dashboard");
  const data = await res.json();

  for (const [key, value] of Object.entries(data)) {
    const element = Variables[key] ?? document.getElementById(key);

    const percentage = (value / (Limits[key][1] - Limits[key][0])) * 100;
    element.style.setProperty("--value", `${percentage}%`);

    if (element.querySelector(".value"))
      element.querySelector(".value").textContent = value;
  }
};

setInterval(loop, 1000);
