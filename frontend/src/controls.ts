import { dispatchToast } from "./toast";
import "./controls.css"

const buttons = {
  download: document.getElementById("download") as HTMLButtonElement,
  openResults: document.getElementById("open-results") as HTMLButtonElement,
  delete: document.getElementById("delete") as HTMLButtonElement,
};

function toggleDisabled(button: HTMLButtonElement, disabled: boolean) {
  button.disabled = disabled;
  button.classList.toggle("disabled", disabled);
}

buttons.download.addEventListener("click", async () => {
  toggleDisabled(buttons.download, true);

  try {
    dispatchToast("Preparing files for download...");
    const res = await fetch("/api/session");
    if (!res.ok) return dispatchToast("Error while downloading.");

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;

    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } finally {
    toggleDisabled(buttons.download, false);
  }
});

buttons.delete.addEventListener("click", async () => {
  toggleDisabled(buttons.delete, true);

  try {
    const res = await fetch("/api/session", { method: "DELETE" });
    if (!res.ok) return dispatchToast("Failed to delete stored files. Try again");

    const data = await res.json();
    if (data.ok) dispatchToast("Deleted stored sessions.");
    else dispatchToast(`Error deleting files. ${data.reason}`);
  } finally {
    toggleDisabled(buttons.delete, false);
  }
});

buttons.openResults.addEventListener("click", () => {
  console.log("Showing popup");
  const resultsPopup = document.getElementById("results-popup") as HTMLDivElement;
  resultsPopup.classList.toggle("hidden", false);
});
