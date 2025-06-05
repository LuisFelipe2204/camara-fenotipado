const camera = document.getElementById("cam-video");

const reloadStream = () => {
  const timestamp = new Date().getTime();
  camera.src = `http://localhost:5000/video?t=${timestamp}`;
};

camera.onerror = () => {
  console.warn("Stream error. Reconnecting in 2s...");
  setTimeout(reloadStream, 2000);
};

reloadStream();
