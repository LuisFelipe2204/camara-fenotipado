const camera = document.getElementById("cam-video");
const camera1 = document.getElementById("cam-video1");

const reloadStream = async () => {
  console.log("A")
  const timestamp = new Date().getTime();
  camera.src = `http://192.168.100.187:5000/video/0?t=${timestamp}`;
};
const reloadStream1 = async () => {
  console.log("B")
  const timestamp = new Date().getTime();
  camera1.src = `http://192.168.100.187:5000/video/1?t=${timestamp}`;
};
camera.onerror = (e) => {
  console.warn(e);
setTimeout(reloadStream, 2000);
};
camera1.onerror = (e) => {
  console.warn(e);
  setTimeout(reloadStream1, 2000);
}

reloadStream();
reloadStream1();
