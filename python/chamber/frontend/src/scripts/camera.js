const camera = document.getElementById("cam-video");
const camera1 = document.getElementById("cam-video1");

let lastUpdate0 = Date.now();
let lastUpdate1 = Date.now();

function reloadStream0() {
  camera.src = `/api/video/0?t=${Date.now()}`;
}
function reloadStream1() {
  camera1.src = `/api/video/1?t=${Date.now()}`;
}

camera.onload = () => {
  lastUpdate0 = Date.now();
};
camera1.onload = () => {
  lastUpdate1 = Date.now();
};

camera.onerror = () => {
  setTimeout(reloadStream0, 2000);
};
camera1.onerror = () => {
  setTimeout(reloadStream1, 2000);
};

setInterval(() => {
  const now = Date.now();
  if (now - lastUpdate0 > 5000) 
    reloadStream0();
  if (now - lastUpdate1 > 5000) 
    reloadStream1();
}, 1000);

reloadStream0();
reloadStream1();
