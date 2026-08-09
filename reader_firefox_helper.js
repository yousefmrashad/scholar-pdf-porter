// Helper for Firefox to handle fetching PDF streams in reader.html context
(function() {
  function z(a) {
    const b = a.indexOf("'");
    if (b < 0) return "";
    const c = a.substring(b + 1);
    if (a.substring(0, b).toLowerCase() !== "utf-8") return "";
    const d = c.indexOf("'");
    if (d < 0) return "";
    try {
      return decodeURIComponent(c.substring(d + 1));
    } catch (e) {
      return "";
    }
  }

  function X(a) {
    return a.startsWith('"') && a.endsWith('"') ? a.substring(1, a.length - 1) : a;
  }

  let Y = false;

  function Z(a) {
    try {
      const parsedUrl = new URL(a);
      const pageUrlParams = new URLSearchParams(window.location.search);
      const allowedFile = pageUrlParams.get("file");
      if (!allowedFile) return false;
      const allowedUrl = new URL(allowedFile);
      // Allow if the origin and pathname match
      return parsedUrl.origin === allowedUrl.origin && parsedUrl.pathname === allowedUrl.pathname;
    } catch (err) {
      return false;
    }
  }

  function ka() {
    const a = new AbortController();
    const b = a.signal;
    const c = setTimeout(() => { a.abort(); }, 30000);
    return { h: b, i: c };
  }

  function la(a, b) {
    const { h: c, i: d } = ka();
    fetch(a, { signal: c }).then(f => {
      clearTimeout(d);
      const e = f.headers;
      if (e.get("Accept-Ranges") === "bytes") {
        Y = true;
      }
      const k = b.postMessage;
      const h = f.body;
      const ma = e.get("Content-Length");
      const na = e.get("Content-Encoding") || "";
      const disposition = e.get("Content-Disposition") || "";
      let t = "";
      for (let m of disposition.split(";")) {
        m = m.trim();
        if (m.startsWith("filename*=")) {
          t = X(z(m.substring(10)));
        } else if (m.startsWith("filename=") && !t) {
          t = X(m.substring(9));
        }
      }
      k.call(b, { type: "pdf", body: h, length: ma, encoding: na, filename: t }, [f.body]);
    }).catch(f => {
      clearTimeout(d);
      b.postMessage({ type: "pdf", error: "fetch pdf: " + f.message });
    });
  }

  function oa(a, b, c, d) {
    if (Y && b >= 0 && c > b) {
      fetch(a, { headers: { Range: `bytes=${b}-${c-1}` } }).then(f => {
        d.postMessage({ type: "pdfrange", body: f.body, begin: b }, [f.body]);
      });
    }
  }

  function pa(a) {
    a.addEventListener("message", b => {
      if (b.data && typeof b.data === "object" && b.data.type === "fetchrange") {
        const c = b.data.url;
        const d = b.data.begin;
        const end = b.data.end;
        if (typeof c === "string" && typeof d === "number" && typeof end === "number" && Z(c)) {
          oa(c, d, end, a);
        }
      }
    });
    a.start();
  }

  window.addEventListener("message", e => {
    if (e.data && typeof e.data === "object") {
      if (e.data.type === "download_pdf") {
        console.log("[ScholarPDF Helper] Downloading PDF from sandboxed iframe:", e.data.filename);
        triggerDownload(e.data.buffer, e.data.filename);
        return;
      }
      if (e.data.printBuffer && e.data.printBuffer instanceof ArrayBuffer) {
        console.log("[ScholarPDF Helper] Printing PDF from printBuffer message");
        triggerPrint(e.data.printBuffer);
        return;
      }
      if (e.data.type === "fetch") {
        const h = e.ports[0];
        if (h && e.source && e.source.parent === window) {
          if (window.localPdfFile) {
            console.log("[ScholarPDF Helper] Loading dropped local file:", window.localPdfFile.name);
            const body = window.localPdfFile.stream();
            h.postMessage({
              type: "pdf",
              body: body,
              length: window.localPdfFile.size,
              encoding: "",
              filename: window.localPdfFile.name
            }, [body]);
            return;
          }
          const url = e.data.url;
          if (typeof url === "string" && Z(url)) {
            console.log("[ScholarPDF Helper] Fetching PDF:", url);
            la(url, h);
            pa(h);
          }
        }
      }
    }
  });
})();

function getDocumentFilename() {
  const titleEl = document.querySelector(".gsr-tb-title");
  let title = titleEl ? titleEl.textContent.trim() : "";
  if (title) {
    title = title.replace(/[/\\?%*:|"<>]/g, "_");
    if (!title.toLowerCase().endsWith(".pdf")) {
      title += ".pdf";
    }
    return title;
  }
  const urlParams = new URLSearchParams(window.location.search);
  const fileUrl = urlParams.get("file");
  if (fileUrl) {
    try {
      const parsed = new URL(fileUrl);
      const name = decodeURIComponent(parsed.pathname.split("/").pop());
      if (name) {
        return name.toLowerCase().endsWith(".pdf") ? name : `${name}.pdf`;
      }
    } catch (e) {}
  }
  return "document.pdf";
}

async function triggerDownload(customBuffer = null, customFilename = "") {
  let filename = customFilename || getDocumentFilename();
  if (!filename.toLowerCase().endsWith(".pdf")) filename += ".pdf";

  if (customBuffer) {
    const blob = new Blob([customBuffer], { type: "application/pdf" });
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { a.remove(); URL.revokeObjectURL(blobUrl); }, 1000);
    return;
  }

  if (window.localPdfFile) {
    const blobUrl = URL.createObjectURL(window.localPdfFile);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = window.localPdfFile.name || filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { a.remove(); URL.revokeObjectURL(blobUrl); }, 1000);
    return;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const fileUrl = urlParams.get("file");
  if (fileUrl) {
    if (fileUrl.startsWith("http://localpdf/")) {
      const localName = decodeURIComponent(fileUrl.substring(16));
      try {
        const file = await getPaper(localName);
        if (file) {
          const blobUrl = URL.createObjectURL(file);
          const a = document.createElement("a");
          a.href = blobUrl;
          a.download = file.name || filename;
          document.body.appendChild(a);
          a.click();
          setTimeout(() => { a.remove(); URL.revokeObjectURL(blobUrl); }, 1000);
          return;
        }
      } catch (err) {}
    }

    try {
      const resp = await fetch(fileUrl);
      const blob = await resp.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { a.remove(); URL.revokeObjectURL(blobUrl); }, 1000);
    } catch (err) {
      console.error("[ScholarPDF Helper] Fetch download failed:", err);
    }
  }
}

async function triggerPrint(customBuffer = null) {
  let blobUrl = "";
  if (customBuffer) {
    const blob = new Blob([customBuffer], { type: "application/pdf" });
    blobUrl = URL.createObjectURL(blob);
  } else if (window.localPdfFile) {
    blobUrl = URL.createObjectURL(window.localPdfFile);
  } else {
    const urlParams = new URLSearchParams(window.location.search);
    const fileUrl = urlParams.get("file");
    if (fileUrl) {
      if (fileUrl.startsWith("http://localpdf/")) {
        const localName = decodeURIComponent(fileUrl.substring(16));
        try {
          const file = await getPaper(localName);
          if (file) {
            blobUrl = URL.createObjectURL(file);
          }
        } catch (e) {}
      } else {
        try {
          const resp = await fetch(fileUrl);
          const blob = await resp.blob();
          blobUrl = URL.createObjectURL(blob);
        } catch (err) {
          console.error("[ScholarPDF Helper] Failed to fetch PDF for printing:", err);
        }
      }
    }
  }

  if (blobUrl) {
    const printIframe = document.createElement("iframe");
    printIframe.style.position = "fixed";
    printIframe.style.top = "-9999px";
    printIframe.style.left = "-9999px";
    printIframe.style.width = "1px";
    printIframe.style.height = "1px";
    printIframe.src = blobUrl;
    printIframe.onload = () => {
      setTimeout(() => {
        try {
          printIframe.contentWindow.focus();
          printIframe.contentWindow.print();
        } catch (err) {
          console.error("[ScholarPDF Helper] Iframe print failed, falling back to window.print():", err);
          window.print();
        }
      }, 300);
      setTimeout(() => {
        printIframe.remove();
        URL.revokeObjectURL(blobUrl);
      }, 120000);
    };
    document.body.appendChild(printIframe);
  } else {
    window.print();
  }
}

// IndexedDB helper functions for library management
const DB_NAME = "ScholarPDFLibrary";
const STORE_NAME = "papers";

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "name" });
      }
    };
    request.onsuccess = (e) => resolve(e.target.result);
    request.onerror = (e) => reject(e.target.error);
  });
}

async function savePaper(file) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readwrite");
    const store = transaction.objectStore(STORE_NAME);
    store.put({ name: file.name, file: file, addedAt: Date.now() });
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

async function getPaper(name) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readonly");
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(name);
    request.onsuccess = (e) => resolve(e.target.result ? e.target.result.file : null);
    request.onerror = (e) => reject(request.error);
  });
}

async function getAllPapers() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readonly");
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();
    request.onsuccess = (e) => resolve(e.target.result || []);
    request.onerror = (e) => reject(request.error);
  });
}

async function deletePaper(name) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readwrite");
    const store = transaction.objectStore(STORE_NAME);
    store.delete(name);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

async function clearPapers() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readwrite");
    const store = transaction.objectStore(STORE_NAME);
    store.clear();
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

// Traversing directories/files dropped recursively
async function traverseEntries(entries, files) {
  for (const entry of entries) {
    if (entry.isFile) {
      const file = await new Promise((resolve) => entry.file(resolve));
      files.push(file);
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      // Read all entries in directory
      let allSubEntries = [];
      const readBatch = async () => {
        const batch = await new Promise((resolve) => reader.readEntries(resolve));
        if (batch.length > 0) {
          allSubEntries = allSubEntries.concat(batch);
          await readBatch();
        }
      };
      await readBatch();
      await traverseEntries(allSubEntries, files);
    }
  }
}

async function handleSelectedFiles(fileList) {
  const pdfFiles = Array.from(fileList).filter(f => f.name.toLowerCase().endsWith(".pdf"));
  if (pdfFiles.length === 0) {
    alert("No PDF files were found.");
    return;
  }

  // Save all papers to IndexedDB
  for (const f of pdfFiles) {
    await savePaper(f);
  }

  // Load the first PDF in the batch
  const firstFile = pdfFiles[0];
  window.location.href = window.location.protocol + "//" + window.location.host + window.location.pathname + "?file=" + encodeURIComponent("http://localpdf/" + firstFile.name);
}

function initDropZone(targetElement, isPlaceholder = false) {
  targetElement.innerHTML = `
    <div class="drop-container ${isPlaceholder ? 'placeholder-drop' : ''}" id="dropContainer">
      <div class="logo-box">
        <img src="icon128.png" alt="Google Scholar PDF Reader Logo">
      </div>
      <h2>${isPlaceholder ? 'No Paper Selected' : 'Google Scholar PDF Reader'}</h2>
      <p>${isPlaceholder ? 'Select a paper from the sidebar library, or drag and drop a new PDF/folder here to add' : 'Drag & drop PDF files or folder here, or browse below'}</p>
      <div style="display: flex; gap: 12px; justify-content: center; margin-bottom: 8px;">
        <button class="browse-btn" id="browseFilesBtn">Browse Files</button>
        <button class="browse-btn" id="browseFolderBtn" style="background-color: #3c4043; color: #e8eaed;">Browse Folder</button>
      </div>
      <input type="file" id="fileInput" accept="application/pdf" multiple style="display:none">
      <input type="file" id="folderInput" webkitdirectory directory style="display:none">
    </div>
  `;

  const dropContainer = targetElement.querySelector("#dropContainer");
  const fileInput = targetElement.querySelector("#fileInput");
  const folderInput = targetElement.querySelector("#folderInput");
  const browseFilesBtn = targetElement.querySelector("#browseFilesBtn");
  const browseFolderBtn = targetElement.querySelector("#browseFolderBtn");

  browseFilesBtn.addEventListener("click", (e) => { e.stopPropagation(); fileInput.click(); });
  browseFolderBtn.addEventListener("click", (e) => { e.stopPropagation(); folderInput.click(); });
  dropContainer.addEventListener("click", (e) => {
    // Only trigger files browse if they clicked on the container empty space or text/logo, not on buttons/inputs
    if (!e.target.closest("button") && !e.target.closest("input")) {
      fileInput.click();
    }
  });

  dropContainer.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropContainer.classList.add("dragover");
  });

  dropContainer.addEventListener("dragleave", () => {
    dropContainer.classList.remove("dragover");
  });

  dropContainer.addEventListener("drop", async (e) => {
    e.preventDefault();
    dropContainer.classList.remove("dragover");

    const items = e.dataTransfer.items;
    const files = [];

    if (items) {
      const entries = [];
      for (let i = 0; i < items.length; i++) {
        const entry = items[i].webkitGetAsEntry();
        if (entry) {
          entries.push(entry);
        }
      }
      await traverseEntries(entries, files);
    } else {
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        files.push(e.dataTransfer.files[i]);
      }
    }

    if (files.length > 0) {
      await handleSelectedFiles(files);
    }
  });

  fileInput.addEventListener("change", async (e) => {
    if (e.target.files.length > 0) {
      await handleSelectedFiles(e.target.files);
    }
  });

  folderInput.addEventListener("change", async (e) => {
    if (e.target.files.length > 0) {
      await handleSelectedFiles(e.target.files);
    }
  });
}

function showDropZone() {
  document.body.classList.add("drop-mode");
  initDropZone(document.body, false);
}

function showPlaceholderDropZone() {
  setupAppLayout(null);
  const rootWrap = document.querySelector(".gsr-root-wrap");
  rootWrap.innerHTML = "";
  initDropZone(rootWrap, true);
}

function createSidebarToggle(appLayout) {
  if (document.querySelector(".sidebar-toggle")) return;

  const toggle = document.createElement("button");
  toggle.className = "sidebar-toggle";
  toggle.setAttribute("title", "Toggle Library Sidebar");
  toggle.innerHTML = `
    <svg viewBox="0 0 24 24">
      <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-4-4H9v-2h6v2zm0-4H9V9h6v2z"/>
    </svg>
  `;

  toggle.addEventListener("click", () => {
    const sidebar = document.getElementById("librarySidebar");
    sidebar.classList.toggle("collapsed");
    localStorage.setItem("gsr-sidebar-collapsed", sidebar.classList.contains("collapsed"));
  });

  appLayout.insertBefore(toggle, appLayout.firstChild);
}

async function renderSidebar(appLayout, activeFileName) {
  let sidebar = document.getElementById("librarySidebar");
  if (!sidebar) {
    sidebar = document.createElement("div");
    sidebar.id = "librarySidebar";
    sidebar.className = "library-sidebar";

    if (localStorage.getItem("gsr-sidebar-collapsed") === "true") {
      sidebar.classList.add("collapsed");
    }

    appLayout.insertBefore(sidebar, appLayout.firstChild);
  }

  const papers = await getAllPapers();

  sidebar.innerHTML = `
    <div class="sidebar-header">
      <h3>My Library</h3>
      <button class="add-paper-btn" id="addPaperBtn" title="Add PDF Files or Folders">+</button>
      <input type="file" id="sidebarFileInput" accept="application/pdf" multiple style="display:none">
      <input type="file" id="sidebarFolderInput" webkitdirectory directory style="display:none">
    </div>
    <div class="search-box">
      <input type="text" id="librarySearch" placeholder="Search papers...">
    </div>
    <div class="paper-list" id="paperList"></div>
    <div class="sidebar-footer">
      <button class="clear-lib-btn" id="clearLibBtn">Clear Library</button>
    </div>
  `;

  const paperList = document.getElementById("paperList");
  const searchInput = document.getElementById("librarySearch");
  const addPaperBtn = document.getElementById("addPaperBtn");
  const sidebarFileInput = document.getElementById("sidebarFileInput");
  const sidebarFolderInput = document.getElementById("sidebarFolderInput");
  const clearLibBtn = document.getElementById("clearLibBtn");

  function updateList(filterText = "") {
    paperList.innerHTML = "";
    const filtered = papers.filter(p => p.name.toLowerCase().includes(filterText.toLowerCase()));

    if (filtered.length === 0) {
      paperList.innerHTML = `<div class="empty-list">No papers found</div>`;
      return;
    }

    filtered.forEach(p => {
      const item = document.createElement("div");
      item.className = "paper-item" + (p.name === activeFileName ? " active" : "");
      item.innerHTML = `
        <div class="paper-icon">
          <svg viewBox="0 0 24 24">
            <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
          </svg>
        </div>
        <div class="paper-title" title="${p.name}">${p.name}</div>
        <button class="delete-btn" data-name="${p.name}" title="Remove from Library">&times;</button>
      `;

      item.addEventListener("click", (e) => {
        if (e.target.classList.contains("delete-btn")) return;
        const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname + "?file=" + encodeURIComponent("http://localpdf/" + p.name);
        window.location.href = newUrl;
      });

      item.querySelector(".delete-btn").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (confirm(`Remove "${p.name}" from your library?`)) {
          await deletePaper(p.name);
          if (p.name === activeFileName) {
            window.location.href = window.location.protocol + "//" + window.location.host + window.location.pathname;
          } else {
            renderSidebar(appLayout, activeFileName);
          }
        }
      });

      paperList.appendChild(item);
    });
  }

  updateList();

  searchInput.addEventListener("input", (e) => updateList(e.target.value));

  // Create dropdown menu element if it doesn't exist
  let dropdown = document.getElementById("addPaperDropdown");
  if (!dropdown) {
    dropdown = document.createElement("div");
    dropdown.id = "addPaperDropdown";
    dropdown.className = "add-paper-dropdown";
    dropdown.innerHTML = `
      <div class="dropdown-item" id="addFilesOpt">
        <svg viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
        Add Files...
      </div>
      <div class="dropdown-item" id="addFolderOpt">
        <svg viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>
        Add Folder...
      </div>
    `;
    document.body.appendChild(dropdown);

    // Event listeners for dropdown options
    dropdown.querySelector("#addFilesOpt").addEventListener("click", () => {
      sidebarFileInput.click();
      dropdown.classList.remove("show");
    });
    dropdown.querySelector("#addFolderOpt").addEventListener("click", () => {
      sidebarFolderInput.click();
      dropdown.classList.remove("show");
    });

    // Close dropdown on click outside
    document.addEventListener("click", (e) => {
      if (!addPaperBtn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
      }
    });
  }

  addPaperBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const rect = addPaperBtn.getBoundingClientRect();
    dropdown.style.top = `${rect.bottom + window.scrollY + 6}px`;
    dropdown.style.left = `${rect.left + window.scrollX - 120}px`;
    dropdown.classList.toggle("show");
  });

  sidebarFileInput.addEventListener("change", async (e) => {
    if (e.target.files.length > 0) {
      await handleImportedFiles(e.target.files);
    }
  });

  sidebarFolderInput.addEventListener("change", async (e) => {
    if (e.target.files.length > 0) {
      await handleImportedFiles(e.target.files);
    }
  });

  async function handleImportedFiles(fileList) {
    const pdfFiles = Array.from(fileList).filter(f => f.name.toLowerCase().endsWith(".pdf"));
    if (pdfFiles.length === 0) {
      alert("No PDF files were found.");
      return;
    }
    for (const f of pdfFiles) {
      await savePaper(f);
    }
    window.location.href = window.location.protocol + "//" + window.location.host + window.location.pathname + "?file=" + encodeURIComponent("http://localpdf/" + pdfFiles[0].name);
  }

  clearLibBtn.addEventListener("click", async () => {
    if (confirm("Are you sure you want to clear your entire library?")) {
      await clearPapers();
      window.location.href = window.location.protocol + "//" + window.location.host + window.location.pathname;
    }
  });
}

function setupAppLayout(activeFileName) {
  let appLayout = document.querySelector(".app-layout");
  if (!appLayout) {
    appLayout = document.createElement("div");
    appLayout.className = "app-layout";
    const rootWrap = document.querySelector(".gsr-root-wrap");
    document.body.appendChild(appLayout);
    appLayout.appendChild(rootWrap);
  }

  renderSidebar(appLayout, activeFileName);
  createSidebarToggle(appLayout);
}

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const fileUrl = urlParams.get("file");

  if (fileUrl) {
    let localFileName = "";
    if (fileUrl.startsWith("http://localpdf/")) {
      localFileName = decodeURIComponent(fileUrl.substring(16));
    } else if (fileUrl.startsWith("http%3A%2F%2Flocalpdf%2F")) {
      localFileName = decodeURIComponent(decodeURIComponent(fileUrl).substring(16));
    }

    if (localFileName) {
      try {
        const file = await getPaper(localFileName);
        if (file) {
          window.localPdfFile = file;
          setupAppLayout(localFileName);
        } else {
          const papers = await getAllPapers();
          if (papers.length > 0) {
            showPlaceholderDropZone();
          } else {
            showDropZone();
          }
          return;
        }
      } catch (err) {
        console.error("Failed to load local file from library DB:", err);
        const papers = await getAllPapers();
        if (papers.length > 0) {
          showPlaceholderDropZone();
        } else {
          showDropZone();
        }
        return;
      }
    }

    const script = document.createElement("script");
    script.src = "/reader-compiled.js";
    script.defer = true;
    document.head.appendChild(script);
  } else {
    try {
      const papers = await getAllPapers();
      if (papers.length > 0) {
        showPlaceholderDropZone();
      } else {
        showDropZone();
      }
    } catch (err) {
      console.error("Failed to read papers for initial state:", err);
      showDropZone();
    }
  }
});

// Intercept clicks on the Full Screen button to trigger HTML5 fullscreen mode
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".gsr-flat-btn");
  if (btn) {
    const svg = btn.querySelector("svg");
    if (svg) {
      const path = svg.querySelector("path");
      if (path && path.getAttribute("d") && path.getAttribute("d").includes("M7 10H5")) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(err => {
            console.error("[ScholarPDF Helper] Failed to enter fullscreen:", err);
          });
        } else {
          document.exitFullscreen().catch(err => {
            console.error("[ScholarPDF Helper] Failed to exit fullscreen:", err);
          });
        }
      }
    }
  }
}, true);

// Intercept clicks on the "Open in Chrome viewer" menu item to bypass reader redirects
document.addEventListener("click", (e) => {
  const item = e.target.closest(".gsr-menu-item");
  if (item && item.textContent.trim() === chrome.i18n.getMessage("1627")) {
    e.preventDefault();
    e.stopPropagation();

    const urlParams = new URLSearchParams(window.location.search);
    const fileUrl = urlParams.get("file");

    if (fileUrl) {
      let decodedUrl = decodeURIComponent(fileUrl);
      if (decodedUrl.includes("localpdf/")) {
        let fileName = "";
        const localIndex = decodedUrl.indexOf("localpdf/");
        if (localIndex !== -1) {
          fileName = decodeURIComponent(decodedUrl.substring(localIndex + 9));
        }
        if (fileName) {
          getPaper(fileName).then(file => {
            if (file) {
              const blobUrl = URL.createObjectURL(file);
              window.location.href = blobUrl;
            } else {
              alert("Local file not found in library.");
            }
          }).catch(err => {
            console.error("[ScholarPDF Helper] Failed to read local PDF:", err);
          });
        }
      } else {
        // Web PDF: notify background script to bypass the next redirect for this tab, then navigate
        chrome.runtime.sendMessage({ type: "bypass-tab-redirect" });
        setTimeout(() => {
          window.location.href = decodedUrl;
        }, 50);
      }
    }
  }
}, true);

// Intercept clicks on the Download button
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".gsr-flat-btn");
  if (btn) {
    const svg = btn.querySelector("svg");
    if (svg) {
      const path = svg.querySelector("path");
      if (path && path.getAttribute("d") && path.getAttribute("d").includes("M14.8 10.3L13.6 9")) {
        e.preventDefault();
        e.stopPropagation();
        console.log("[ScholarPDF Helper] Download button clicked via direct interceptor");
        await triggerDownload();
      }
    }
  }
}, true);

// Intercept clicks on the Print button
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".gsr-flat-btn");
  if (btn) {
    const svg = btn.querySelector("svg");
    if (svg) {
      const path = svg.querySelector("path");
      if (path && path.getAttribute("d") && path.getAttribute("d").includes("M14 7.5V4.8")) {
        e.preventDefault();
        e.stopPropagation();
        console.log("[ScholarPDF Helper] Print button clicked via direct interceptor");
        await triggerPrint();
      }
    }
  }
}, true);


