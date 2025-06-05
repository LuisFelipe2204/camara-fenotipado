const imagePopup = document.getElementById("image-popup");

const photoData = {
  RGB: document.getElementById("popup-rgb"),
  RE: document.getElementById("popup-re"),
  RGN: document.getElementById("popup-rgn"),
  total: document.getElementById("popup-total"),
};


const createImageCarousel = (photos) => {
  const wrapper = document.querySelector('.image-view-wrapper');
  wrapper.innerHTML = ''; // Clear existing content

  if (!photos.length) {
    wrapper.textContent = 'No photos available.';
    return;
  }

  let currentIndex = 0;

  // Create title element
  const title = document.createElement('div');
  title.classList.add('image-title');
  title.textContent = photos[0].filename;
  title.style.textAlign = 'center';
  title.style.marginBottom = '10px';
  title.style.fontWeight = 'bold';

  // Create image element
  const img = document.createElement('img');
  img.src = `data:${photos[0].content_type};base64,${photos[0].content}`;
  img.style.maxWidth = '100%';
  img.style.cursor = 'pointer';
  img.style.display = 'block';
  img.style.margin = '0 auto';

  // Click to cycle
  img.addEventListener('click', () => {
    currentIndex = (currentIndex + 1) % photos.length;
    const current = photos[currentIndex];
    img.src = `data:${current.content_type};base64,${current.content}`;
    title.textContent = current.filename;
  });

  wrapper.appendChild(title);
  wrapper.appendChild(img);
}

document.addEventListener("progressDone", async () => {
  imagePopup.classList.remove("popup-hidden");

  const res = await fetch("/api/dashboard/photos", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  /**
   * @type {{
   *   photo_counts: {
   *     RGB: number,
   *     RE: number,
   *     RGN: number
   *   },
   *   photos: Array<{
   *     filename: string,
   *     content: string,
   *     content_type: "image/jpeg" | "image/png"
   *   }>
   * }}
   */
  const data = await res.json();

  photoData.RGB.textContent = data.photo_counts.RGB;
  photoData.RE.textContent = data.photo_counts.RE;
  photoData.RGN.textContent = data.photo_counts.RGN;
  photoData.total.textContent =
    data.photo_counts.RGB + data.photo_counts.RE + data.photo_counts.RGN;

  console.log(data);
  createImageCarousel(data.photos);
});

document.addEventListener("click", function (event) {
  const popup = document.getElementById("image-popup");
  const content = popup.querySelector(".popup-content");

  if (
    !popup.classList.contains("popup-hidden") &&
    !content.contains(event.target)
  ) {
    popup.classList.add("popup-hidden");
  }
});
