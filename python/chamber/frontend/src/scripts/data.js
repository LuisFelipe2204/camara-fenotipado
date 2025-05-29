const Variables = {
  temp: document.getElementById("temp"),
  hum: document.getElementById("hum"),
  white_lux: document.getElementById("white_lux"),
  ir_lux: document.getElementById("ir_lux"),
  uv_lux: document.getElementById("uv_lux"),
  running: document.getElementById("running"),
  progress: document.getElementById("progress"),
  direction: document.getElementById("direction"),
  angle: document.getElementById("angle"),
};

const Limits = {
  temp: [-10, 50],
  hum: [0, 100],
  white_lux: [0, 1000],
  ir_lux: [0, 1000],
  uv_lux: [0, 16],
  running: [0, 1],
  direction: [-1, 1],
  angle: [0, 300],
  progress: [0, 100],
};

const States = {
  running: {
    0: "Detenido",
    1: "Ejecutando",
  },
};

const donePopup = document.getElementById("done-popup");

let oldDone = false;

const loop = async () => {
  const res = await fetch("/api/dashboard");
  if (!res.ok) {
    console.error("Error fetching data");
    return;
  }
  const data = await res.json();

  for (const [key, value] of Object.entries(data)) {
    /**
     * @type {HTMLElement | null}
     */
    const element = Variables[key] ?? document.getElementById(key);
    if (!element) {
      console.warn(`Element for ${key} not found`);
      continue;
    }

    const percentage = (value / (Limits[key][1] - Limits[key][0])) * 100;
    element.style.setProperty("--value", `${percentage}%`);
    element.setAttribute("data-value", value);

    if (element.querySelector(".value"))
      element.querySelector(".value").textContent =
        value + " " + (element.getAttribute("data-unit") || "");
    if (element.querySelector(".state")) {
      element.querySelector(".state").textContent = States[key][value & 1];
    }
  }

  let done = data.progress === 100;
  if (!oldDone && done) {
    btn.classList.toggle("active", false);
    const event = new CustomEvent("progressDone");

    await fetch("/api/dashboard/running?value=0", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    document.dispatchEvent(event);
    btn.classList.toggle("active", true);
  }
};

setInterval(loop, 500);
