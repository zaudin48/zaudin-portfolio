// static/js/main.js
document.addEventListener("DOMContentLoaded", function(){
  // typed.js tagline
  if (document.getElementById("typed")) {
    new Typed('#typed', {
      strings: ['Frontend Developer', 'Fast UI builder', 'Event Manager', 'Java/Python basics'],
      typeSpeed: 60,
      backSpeed: 35,
      backDelay: 1600,
      loop: true
    });
  }

  // fill year
  const y = new Date().getFullYear();
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = y;

  // fetch projects and fill grid
  const grid = document.getElementById("projectsGrid");
  if (grid) {
    fetch("/api/projects").then(r => r.json()).then(items => {
      if (!items.length) grid.innerHTML = '<p class="muted">No projects yet. Add via admin panel.</p>';
      items.forEach(p => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
          ${p.img_path ? `<img src="/${p.img_path}" alt="${escapeHtml(p.title)}" />` : ""}
          <h3>${escapeHtml(p.title)}</h3>
          <p class="muted">${escapeHtml(p.description || "")}</p>
          ${p.link ? `<p><a href="${p.link}" target="_blank" class="btn ghost">Open</a></p>` : ""}
        `;
        grid.appendChild(card);

        // simple fade-up animation with GSAP
        gsap.from(card, {opacity:0, y:20, duration:0.8, ease:"power2.out", stagger:0.06});
      });
    });
  }


});

function escapeHtml(str){
  if(!str) return "";
  return str.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

