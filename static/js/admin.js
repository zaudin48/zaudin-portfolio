// Admin JS — Final Clean Crash-Proof Version

document.addEventListener("DOMContentLoaded", () => {

  /* ====== ELEMENTS ====== */
  const projectsTable = document.getElementById("projectsTable");
  const projectsCount = document.getElementById("projectsCount"); // optional
  const modal = document.getElementById("projectModal");
  const overlay = document.getElementById("modalOverlay");
  const addBtn = document.getElementById("addProjectBtn");
  const cancelModal = document.getElementById("cancelModal");
  const projectForm = document.getElementById("projectForm");
  const deleteFromModal = document.getElementById("deleteFromModal");

  let projects = [];

  /* ====== SAFE EVENT LISTENERS ====== */
  if (addBtn)
    addBtn.addEventListener("click", () => openModal());

  if (cancelModal)
    cancelModal.addEventListener("click", closeModal);

  if (overlay)
    overlay.addEventListener("click", closeModal);

  if (deleteFromModal)
    deleteFromModal.addEventListener("click", () => {
      const id = document.getElementById("projId").value;
      if (id) {
        deleteProject(id);
        closeModal();
      }
    });

  /* ====== MODAL CONTROL ====== */
  function openModal(mode = "add", project = null) {
    if (!overlay || !modal) return;

    overlay.style.display = "flex";
    modal.style.display = "flex";
    document.body.style.overflow = "hidden";

    const title = document.getElementById("modalTitle");
    if (title) title.textContent =
      mode === "add" ? "Add Project" : "Edit Project";

    if (deleteFromModal)
      deleteFromModal.classList.toggle("hidden", mode === "add");

    if (projectForm) projectForm.reset();

    if (project) {
      document.getElementById("projId").value = project.id;
      document.getElementById("projTitle").value = project.title;
      document.getElementById("projDesc").value = project.description || "";
      document.getElementById("projLink").value = project.link || "";
    }
  }

  function closeModal() {
    if (!overlay || !modal) return;

    overlay.style.display = "none";
    modal.style.display = "none";
    document.body.style.overflow = "";
    if (projectForm) projectForm.reset();
  }

  /* ====== LOAD PROJECTS ====== */
  function loadProjects() {
    fetch("/api/projects")
      .then((res) => res.json())
      .then((data) => {
        projects = data || [];
        displayProjects(projects);
      })
      .catch(() => {
        if (projectsTable)
          projectsTable.innerHTML =
            '<div class="muted">Failed to load projects.</div>';
      });
  }

  /* ====== DISPLAY PROJECTS ====== */
  function displayProjects(list) {
    if (!projectsTable) return;

    projectsTable.innerHTML = "";

    if (projectsCount)
      projectsCount.textContent = list.length;

    if (!list.length) {
      projectsTable.innerHTML =
        '<div class="muted">No projects yet. Click "New project".</div>';
      return;
    }

    list.forEach((p) => {
      const row = document.createElement("div");
      row.className = "project-row";

      row.innerHTML = `
        <div class="project-thumb">
          <img src="${p.img_url || "/static/uploads/default_pfp.png"}">
        </div>

        <div class="project-meta">
          <strong>${escapeHtml(p.title)}</strong>
          <div class="muted small">${escapeHtml(p.description || "")}</div>
        </div>

        <div class="project-actions">
          <button class="btn ghost edit-btn">Edit</button>
          <button class="btn danger ghost delete-btn">Delete</button>
        </div>
      `;

      // edit
      row.querySelector(".edit-btn").addEventListener("click", () =>
        openModal("edit", p)
      );

      // delete
      row.querySelector(".delete-btn").addEventListener("click", () =>
        deleteProject(p.id)
      );

      projectsTable.appendChild(row);
    });
  }

  /* ====== ADD / EDIT PROJECT ====== */
  if (projectForm) {
    projectForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const data = new FormData(projectForm);
      const id = data.get("id");
      const url = id ? "/admin/edit-project" : "/admin/upload";

      fetch(url, { method: "POST", body: data })
        .then((res) => {
          if (res.ok) {
            closeModal();
            loadProjects();
          } else {
            res.text().then((t) => alert("Error: " + t));
          }
        })
        .catch(() => alert("Network error"));
    });
  }
  // File input helpers (add at end of DOMContentLoaded section)
(function(){
  const fileInput = document.getElementById('projImage');
  const fileName = document.getElementById('fileName');
  const fileBtn  = document.getElementById('fileBtn');
  const preview  = document.getElementById('filePreview');

  if (!fileInput) return;

  // clicking the visible "Browse" triggers the hidden file input (safe fallback)
  if (fileBtn) {
    fileBtn.addEventListener('click', (e) => {
      e.preventDefault();
      fileInput.click();
    });
  }

  // update filename and optionally show preview
  fileInput.addEventListener('change', () => {
    const f = fileInput.files && fileInput.files[0];
    fileName.textContent = f ? f.name : 'No file chosen';

    // image preview (optional)
    if (preview) {
      if (f && f.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          preview.src = ev.target.result;
          preview.style.display = 'block';
        };
        reader.readAsDataURL(f);
      } else {
        preview.style.display = 'none';
        preview.src = '';
      }
    }
  });
})();


  /* ====== DELETE ====== */
  function deleteProject(id) {
    if (!confirm("Delete project #" + id + "?")) return;

    fetch("/admin/delete-project", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "project_id=" + encodeURIComponent(id),
    }).then((res) => {
      if (res.ok) loadProjects();
      else res.text().then((t) => alert(t));
    });
  }

  /* ====== SEARCH ====== */
  const searchInput = document.getElementById("searchProjects");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase();
      const filtered = projects.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          (p.description || "").toLowerCase().includes(q)
      );
      displayProjects(filtered);
    });
  }
/* ====== CONTACT INFO UPDATE (NEW) ====== */
const contactForm = document.getElementById("adminContactForm");
const contactStatus = document.getElementById("contactStatus");

if (contactForm) {
  contactForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const data = new FormData(contactForm);

    fetch("/admin/update-contact", {
      method: "POST",
      body: data
    })
    .then((res) => {
      if (res.ok) {
        if (contactStatus) {
          contactStatus.textContent = "Saved ✔";
          contactStatus.style.color = "#6ee7b7";

          setTimeout(() => {
            contactStatus.textContent = "";
          }, 2500);
        }
      } else {
        res.text().then((t) => alert("Error: " + t));
      }
    })
    .catch(() => alert("Network error"));
  });
}

  /* ====== INIT ====== */
  loadProjects();
});

/* Escape HTML */
function escapeHtml(str) {
  return str
    ? str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
    : "";
}
