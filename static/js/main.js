(function () {
  const API = (typeof API_URL !== "undefined" && API_URL) ? API_URL : "";

  document.addEventListener("DOMContentLoaded", function () {

    /* ---------------------- Typed Effect ---------------------- */
    if (document.getElementById("typed")) {
      new Typed("#typed", {
        strings: [
          "Frontend Developer",
          "Event Manager",
          "Fast UI builder"
        ],
        typeSpeed: 60,
        backSpeed: 35,
        backDelay: 1600,
        loop: true
      });
    }

    /* ---------------------- Year Update ---------------------- */
    const year = document.getElementById("year");
    if (year) year.textContent = new Date().getFullYear();


 
// Load profile pic safely
fetch(API + "/api/profile")
  .then(r => r.json())
  .then(data => {
    const img = document.getElementById("profilePic");
    if (!img) return;

    // FIX 1 — NEVER change image if backend sends empty pfp
    if (!data || !data.pfp || data.pfp.trim() === "") {
      // DO NOT override user's current image
      return;
    }

    // FIX 2 — Use correct URL
    let url = data.pfp.startsWith("/")
      ? data.pfp
      : "/" + data.pfp;

    img.src = url;
  })
  .catch(() => {
    // FIX 3 — Only use fallback if page has NO image yet
    const img = document.getElementById("profilePic");
    if (img && !img.src.includes("uploads")) {
      img.src = "/static/uploads/default_pfp.png";
    }
  });



    /* ---------------------- Projects Loader ---------------------- */
    const grid = document.getElementById("projectsGrid");
    if (grid) {
      fetch(API + "/api/projects")
        .then(res => res.json())
        .then(items => {
          if (!items || items.length === 0) {
            grid.innerHTML = `<p class="muted">No projects yet. Add via admin.</p>`;
            return;
          }

          items.forEach(p => {
            const card = document.createElement("div");
            card.className = "card";

            let imgSrc = "";
            if (p.img_url) {
              imgSrc = p.img_url.startsWith("http")
                ? p.img_url
                : API + p.img_url;
            }

            card.innerHTML = `
              ${imgSrc ? `<img src="${imgSrc}" alt="${escapeHtml(p.title)}">` : ""}
              <h3>${escapeHtml(p.title)}</h3>
              <p class="muted">${escapeHtml(p.description || "")}</p>
              ${p.link ? `<p><a class="btn ghost" href="${p.link}" target="_blank">Open</a></p>` : ""}
            `;

            grid.appendChild(card);

            if (window.gsap) {
              gsap.from(card, {
                opacity: 0,
                y: 20,
                duration: 0.7,
                ease: "power2.out"
              });
            }
          });
        })
        .catch(err => {
          console.warn("projects fetch failed:", err);
          grid.innerHTML = `<p class="muted">Unable to load projects.</p>`;
        });
    }
  });

  /* ---------------------- Escape HTML ---------------------- */
  function escapeHtml(s) {
    if (!s) return "";
    return s
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

})();
