/* ═══════════════════════════════════════
   几何星球AUTO — 前端交互
   原生 JS，零依赖
   ═══════════════════════════════════════ */

// ── 工具函数 ──
function formatNum(n) {
  if (n == null || isNaN(n)) return "0";
  return Number(n).toLocaleString("zh-CN");
}

function escapeHtml(s) {
  return (s || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ── Toast ──
function showToast(msg, type) {
  if (type === void 0) type = "info";
  var el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast " + type + " show";
  setTimeout(function () { el.className = "toast"; }, 3000);
}

// ── Modal 点击背景关闭 ──
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("modal")) {
    e.target.classList.remove("active");
  }
});
