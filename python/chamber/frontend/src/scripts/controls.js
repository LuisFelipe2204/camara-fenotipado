const downloadBtn = document.getElementById("download-zip")
const popupBtn = document.getElementById("open-popup")
const deleteBtn = document.getElementById("delete-files")

// Open the results popup
popupBtn.addEventListener("click", () => {
    imagePopup.classList.remove("popup-hidden");
    console.log("Opening popup")
});

// Download the ZIP of all images
downloadBtn.addEventListener("click", async () => {
    downloadBtn.disabled = true
    downloadBtn.classList.toggle("disabled", true)
    try {
        document.dispatchEvent(new CustomEvent("toast", { detail: { msg: "Preparing files for download..." } }))
        const res = await fetch("/api/session/download")
        if (!res.ok) return document.dispatchEvent(new CustomEvent("toast", { detail: { msg: "Error while downloading" } }));
        
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

deleteBtn.addEventListener("click", async () => {
    deleteBtn.disabled = true;
    deleteBtn.classList.toggle("disabled", true)

    try {
        const res = await fetch("/api/session/delete", {
            method: "DELETE"
        });
        if (!res.ok) return document.dispatchEvent(new CustomEvent("toast", {detail: {msg: "Failed to delete stored files. Try again."}}))

        const data = await res.json()
        console.log("Delete req", data)
        if (data.ok) {
            console.log("Sending toasst")
            document.dispatchEvent(new CustomEvent("toast", { detail: { msg: "Deleted stored sessions." } }))
        }
        else {
            document.dispatchEvent(new CustomEvent("toast", { detail: { msg: `Error deleting files. ${data.reason}` } }))
        }
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.classList.toggle("disabled", false)
    }
})

// Display a toast
let currentToastHide = -1;
document.addEventListener("toast", (e) => {
    let toast = document.getElementById("toast")
    if (currentToastHide !== -1) clearTimeout(currentToastHide);
    console.log("Toastin:", e.detail.msg);
    toast.innerText = e.detail.msg
    toast.classList.toggle("popup-hidden", false);

    currentToastHide = setTimeout(() => {
        toast.classList.toggle("popup-hidden", true);
        currentToastHide = -1;
    }, 5000)
})