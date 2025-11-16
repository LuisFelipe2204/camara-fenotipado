const camera = document.getElementById("cam-video");
const camera1 = document.getElementById("cam-video1");

function reloadStream0() {
  camera.src = `/api/video/0?t=${Date.now()}`;
}
function reloadStream1() {
  camera1.src = `/api/video/1?t=${Date.now()}`;
}

camera.onerror = () => {
  setTimeout(reloadStream0, 2000);
};
camera1.onerror = () => {
  setTimeout(reloadStream1, 2000);
};

setInterval(() => {
  reloadStream0();
  reloadStream1();
}, 10000);

reloadStream0();
reloadStream1();