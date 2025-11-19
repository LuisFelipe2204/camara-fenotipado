const btn = document.querySelector("#running .border");

btn.addEventListener("click", async () => {
  if (!btn.classList.contains("active")) {
    return;
  }

  btn.classList.toggle("active", false);
  const state = btn.querySelector(".state").textContent == "Ejecutando" ? 1 : 0; // Current state
  await fetch(`/api/dashboard/running?value=${state ^ 1}`, { // Request a change to the opposite state
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });
  btn.classList.toggle("active", true);

  if (state ^ 1 === 0) {
    const event = new CustomEvent("progressDone");
    document.dispatchEvent(event);
  }
});
