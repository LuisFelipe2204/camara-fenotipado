const downloadBtn = document.getElementById("download-zip")
const popupBtn = document.getElementById("open-popup")

popupBtn.addEventListener("click", () => {
    imagePopup.classList.remove("popup-hidden");
    console.log("Opening popup")
});

downloadBtn.addEventListener("click", async () => {
    downloadBtn.disabled = true
    downloadBtn.classList.toggle("disabled", true)
    try {
        const res = await fetch("/api/session/download")
        if (!res.ok) return;
        
        const blob = await res.blob()
        const blobUrl = URL.createObjectURL(blob)
        
        const anchor = document.createElement("a");
        anchor.href = blobUrl;
        
        document.body.appendChild(anchor)
        anchor.click()
        anchor.remove()
        URL.revokeObjectURL(blobUrl)
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.classList.toggle("disabled", false)
    }
})