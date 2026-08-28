document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("activate-form");
  const btn = document.getElementById("activate-btn");

  if (!form || !btn) return;

  form.addEventListener("submit", () => {
    // Prevent double-submit / double-click while the POST is in flight.
    btn.disabled = true;
    btn.textContent = "Activating...";
  });
});
