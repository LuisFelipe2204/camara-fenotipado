const downloadBtn = document.getElementById("download-zip")
const popupBtn = document.getElementById("open-popup")
const deleteBtn = document.getElementById("delete-files")

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

deleteBtn.addEventListener("click", async () => {
    deleteBtn.disabled = true;
    deleteBtn.classList.toggle("disabled", true)

    try {
        const res = await fetch("/api/session/delete", {
            method: "DELETE"
        });
        if (!res.ok) return dispatchEvent(new CustomEvent("toast", {detail: {msg: "Failed to delete stored files. Try again."}}))

        const data = await res.json()
        console.log("Delete req", data)
        if (data.ok) {
            dispatchEvent(new CustomEvent("toast", { detail: { msg: "Deleted stored sessions." } }))
        }
        else {
            dispatchEvent(new CustomEvent("toast", { detail: { msg: `Error deleting files. ${data.reason}` } }))
        }
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.classList.toggle("disabled", false)
    }
})

document.addEventListener("toast", (e) => {
    console.log("Toastin")
    let toast = document.getElementById("toast")
    toast.textContent = e.detail.msg
    toast.classList.toggle("popup-hidden", false);

    setTimeout(() => {
        toast.classList.toggle("popup-hidden", true);
    }, 5000)
})