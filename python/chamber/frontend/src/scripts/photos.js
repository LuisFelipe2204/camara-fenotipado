const imagePopup = document.getElementById("image-popup");
const wrapper = document.getElementById("image-view-wrapper");
const loader = document.getElementById("image-view-loader");

const imageSideTitle = document.querySelector("#image-view-side .image-title");
const imageSideImage = document.querySelector("#image-view-side .image-image");

const imageTopTitle = document.querySelector("#image-view-top .image-title");
const imageTopImage = document.querySelector("#image-view-top .image-image");

const imageRETitle = document.querySelector("#image-view-re .image-title");
const imageREImage = document.querySelector("#image-view-re .image-image");

const imageRGNTitle = document.querySelector("#image-view-rgn .image-title");
const imageRGNImage = document.querySelector("#image-view-rgn .image-image");

const currentPages = document.getElementById("current-page")
const totalPages = document.getElementById("total-pages")

let carouselIndex = 0;
let max_length = 0;
const images = {
  RE: [],
  RGN: [],
  RGB: [],
  RGBT: [],
};

const photoData = {
  RGB: document.getElementById("popup-rgb"),
  RGBT: document.getElementById("popup-rgbt"),
  RE: document.getElementById("popup-re"),
  RGN: document.getElementById("popup-rgn"),
};

/**
 * 
 * @param {number} maxAttempts The maximum amount of tries
 * @param {number} delayMs The delay between polling requests in milliseconds
 * @returns {Promise<{ 
 *   photo_counts: { 
 *     RGB: number, 
 *     RGBT: number, 
 *     RE: number, 
 *     RGN: number 
 *   },
 *   photos: { 
 *     RGB: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>, 
 *     RGBT: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>, 
 *     RE: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>, 
 *     RGN: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>
 *   }, 
 *   completed: boolean 
 *  }>}
 */
async function pollPhotos(maxAttempts = 60, delayMs = 2000) {
  let attempts = 0;
  while (attempts < maxAttempts) {
    attempts++;

    try {
      const res = await fetch("/api/dashboard/photos", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await res.json();

      if (data.completed) return data;
    } catch (err) {
      console.error("Error polling photos:", err);
    }

    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }

  console.warn("Max polling attempts reached without completion");
  return null;
}

function resetImageDisplay() {
  imageRETitle.textContent = images.RE[carouselIndex]?.title || "";
  imageSideTitle.textContent = images.RGB[carouselIndex]?.title || "";
  imageTopTitle.textContent = images.RGBT[carouselIndex]?.title || "";
  imageRGNTitle.textContent = images.RGN[carouselIndex]?.title || "";

  imageREImage.src = images.RE[carouselIndex]?.image || "";
  imageSideImage.src = images.RGB[carouselIndex]?.image || "";
  imageTopImage.src = images.RGBT[carouselIndex]?.image || "";
  imageRGNImage.src = images.RGN[carouselIndex]?.image || "";
}

document.addEventListener("resetPopup", async () => {
  photoData.RGB.textContent = "...";
  photoData.RGBT.textContent = "...";
  photoData.RE.textContent = "...";
  photoData.RGN.textContent = "...";

  images.RGB = []
  images.RGBT = []
  images.RE = []
  images.RGN = []
})

let transferring = false;

document.addEventListener("progressDone", async () => {
  imagePopup.classList.remove("popup-hidden");

  transferring = true;
  wrapper.style.display = "none";
  loader.style.display = "flex"
  const finalData = await pollPhotos();
  if (!finalData) {
    console.warn("Polling did not complete in time");
    return;
  }
  wrapper.style.display = "grid";
  loader.style.display = "none"
  transferring = false;
  
  const data = finalData;
  carouselIndex = 0;
  max_length = Math.max(
    images.RGB.length,
    images.RGBT.length,
    images.RE.length,
    images.RGN.length
  );

  const mapImages = (image) => ({
    title: image ? image.filename : "",
    image: image ? `data:${image.content_type};base64,${image.content}` : "",
  });

  images.RE = data.photos.RE.map(mapImages);
  images.RGN = data.photos.RGN.map(mapImages);
  images.RGB = data.photos.RGB.map(mapImages);
  images.RGBT = data.photos.RGBT.map(mapImages);

  max_length = Math.max(
    images.RGB.length,
    images.RGBT.length,
    images.RE.length,
    images.RGN.length
  );
  totalPages.textContent = max_length;

  photoData.RGB.textContent = images.RGB.length;
  photoData.RGBT.textContent = images.RGBT.length;
  photoData.RE.textContent = images.RE.length;
  photoData.RGN.textContent = images.RGN.length;

  resetImageDisplay()
});

wrapper.addEventListener("click", () => {
  // Set the next image on the elements on click
  carouselIndex = (carouselIndex + 1) % max_length;
  currentPages.textContent = carouselIndex + 1;

  resetImageDisplay()
});

imagePopup.addEventListener("click", (event) => {
  const content = imagePopup.querySelector(".popup-content");
  if (!imagePopup.classList.contains("popup-hidden") && !content.contains(event.target)) {
    // Close the photos popup after transferring all photos
    if (transferring) {
      document.dispatchEvent(new CustomEvent("toast", { detail: { msg: "Wait for image transfer to finish before closing." } }))
      return;
    }
    imagePopup.classList.add("popup-hidden");
  }
});
