const imagePopup = document.getElementById("image-popup");
const wrapper = document.getElementById("image-view-wrapper");

const imageSideTitle = document.querySelector("#image-view-side .image-title");
const imageSideImage = document.querySelector("#image-view-side .image-image");

const imageTopTitle = document.querySelector("#image-view-top .image-title");
const imageTopImage = document.querySelector("#image-view-top .image-image");

const imageRETitle = document.querySelector("#image-view-re .image-title");
const imageREImage = document.querySelector("#image-view-re .image-image");

const imageRGNTitle = document.querySelector("#image-view-rgn .image-title");
const imageRGNImage = document.querySelector("#image-view-rgn .image-image");

let carouselIndex = 0;
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

document.addEventListener("progressDone", async () => {
  // Fetch all images when progress is done
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
   *     RGBT: number,
   *     RE: number,
   *     RGN: number
   *   },
   *   photos: {
   *     RGB: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>,
   *     RGBT: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>,
   *     RE: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>,
   *     RGN: Array<{ filename: string, content: string, content_type: "image/jpeg" | "image/png" }>
   *   }
   * }}
   */
  const data = await res.json();
  console.log(data)
  carouselIndex = 0;

  photoData.RGB.textContent = data.photo_counts.RGB;
  photoData.RGBT.textContent = data.photo_counts.RGBT;
  photoData.RE.textContent = data.photo_counts.RE;
  photoData.RGN.textContent = data.photo_counts.RGN;

  const mapImages = (image) => ({
    title: image ? image.filename : "",
    image: image ? `data:${image.content_type};base64,${image.content}` : "",
  });

  images.RE = data.photos.RE.map(mapImages);
  images.RGN = data.photos.RGN.map(mapImages);
  images.RGB = data.photos.RGB.map(mapImages);
  images.RGBT = data.photos.RGBT.map(mapImages);

  console.log(images);

  imageRETitle.textContent = images.RE[carouselIndex]?.title || "";
  imageSideTitle.textContent = images.RGB[carouselIndex]?.title || "";
  imageTopTitle.textContent = images.RGBT[carouselIndex]?.title || "";
  imageRGNTitle.textContent = images.RGN[carouselIndex]?.title || "";

  imageREImage.src = images.RE[carouselIndex]?.image || "";
  imageSideImage.src = images.RGB[carouselIndex]?.image || "";
  imageTopImage.src = images.RGBT[carouselIndex]?.image || "";
  imageRGNImage.src = images.RGN[carouselIndex]?.image || "";
});

wrapper.addEventListener("click", (event) => {
  // Set the next image on the elements on click
  carouselIndex = (carouselIndex + 1) % images.RGB.length;

  imageRETitle.textContent = images.RE[carouselIndex]?.title || "";
  imageSideTitle.textContent = images.RGB[carouselIndex]?.title || "";
  imageTopTitle.textContent = images.RGBT[carouselIndex]?.title || "";
  imageRGNTitle.textContent = images.RGN[carouselIndex]?.title || "";

  imageREImage.src = images.RE[carouselIndex]?.image || "";
  imageSideImage.src = images.RGB[carouselIndex]?.image || "";
  imageTopImage.src = images.RGBT[carouselIndex]?.image || "";
  imageRGNImage.src = images.RGN[carouselIndex]?.image || "";
});

document.addEventListener("click", (event) => {
  // Close the popup when clicked outside
  const popup = document.getElementById("image-popup");
  const content = popup.querySelector(".popup-content");

  if (
    !popup.classList.contains("popup-hidden") &&
    !content.contains(event.target)
  ) {
    popup.classList.add("popup-hidden");
  }
});
