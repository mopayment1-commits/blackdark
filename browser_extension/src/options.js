import { DEFAULT_API_BASE, getApiBase } from "./api.js";

const input = document.getElementById("apiBase");
const status = document.getElementById("status");

getApiBase().then((base) => {
  input.value = base || DEFAULT_API_BASE;
});

document.getElementById("save").addEventListener("click", async () => {
  const apiBase = (input.value || DEFAULT_API_BASE).trim().replace(/\/$/, "");
  await chrome.storage.sync.set({ apiBase });
  status.textContent = "Saved.";
});
