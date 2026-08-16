// Small, dependency-free helper for the 6 individual OTP boxes:
// moves focus forward/back as digits are typed, supports pasting the
// whole code at once, and combines everything into the hidden #otp
// field right before the form submits.

(function () {
  const boxes = Array.from(document.querySelectorAll(".rx-slip__digit"));
  const combined = document.getElementById("otp-combined");
  const form = document.getElementById("otp-form");

  if (!boxes.length || !form) return;

  boxes.forEach((box, i) => {
    box.addEventListener("input", () => {
      box.value = box.value.replace(/[^0-9]/g, "").slice(0, 1);
      if (box.value && i < boxes.length - 1) {
        boxes[i + 1].focus();
      }
    });

    box.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !box.value && i > 0) {
        boxes[i - 1].focus();
      }
    });

    box.addEventListener("paste", (e) => {
      e.preventDefault();
      const digits = (e.clipboardData.getData("text") || "").replace(/[^0-9]/g, "").split("");
      boxes.forEach((b, idx) => { b.value = digits[idx] || ""; });
      const next = boxes[Math.min(digits.length, boxes.length - 1)];
      if (next) next.focus();
    });
  });

  form.addEventListener("submit", () => {
    combined.value = boxes.map((b) => b.value).join("");
  });
})();
