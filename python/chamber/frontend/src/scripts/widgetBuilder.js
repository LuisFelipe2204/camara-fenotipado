const Template = {
  thermometer: document.getElementById("temp-thermometer"),
  waterdrop: document.getElementById("temp-waterdrop"),
  bulb: document.getElementById("temp-bulb"),
  progress: document.getElementById("temp-progress"),
  value: document.getElementById("temp-value"),
};

const Widgets = {
  thermometer: document.querySelectorAll(".temp-thermometer"),
  waterdrop: document.querySelectorAll(".temp-waterdrop"),
  bulb: document.querySelectorAll(".temp-bulb"),
  progress: document.querySelectorAll(".temp-progress"),
  value: document.querySelectorAll(".temp-value"),
};

/**
 * @param {Element} widget
 * @param {HTMLElement} template
 */
const buildWidget = (widget, template) => {
  const clone = template.content.cloneNode(true);

  clone.querySelector(".title").textContent = widget.getAttribute("data-title");
  clone.querySelector(".value").textContent = widget.getAttribute("data-value");
  widget.append(clone);
};

Object.entries(Template).forEach(([key, template]) => {
  Widgets[key].forEach((widget) => {
    buildWidget(widget, template);
  });
});