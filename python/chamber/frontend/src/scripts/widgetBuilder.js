const Template = {
  thermometer: document.getElementById("temp-thermometer"),
  waterdrop: document.getElementById("temp-waterdrop"),
  bulb: document.getElementById("temp-bulb"),
};

const Widgets = {
  thermometer: document.querySelectorAll(".temp-thermometer"),
  waterdrop: document.querySelectorAll(".temp-waterdrop"),
  bulb: document.querySelectorAll(".temp-bulb"),
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

Widgets.thermometer.forEach((widget) => buildWidget(widget, Template.thermometer));
Widgets.waterdrop.forEach((widget) => buildWidget(widget, Template.waterdrop));
Widgets.bulb.forEach((widget) => buildWidget(widget, Template.bulb));
