# Google Scholar PDF Reader - Firefox Porting Patcher

This repository contains a Python-based automated patching utility to port the official Google Scholar PDF Reader extension (packaged as a `.zip` or `.crx`) to Firefox-based browsers (such as Firefox, Zen Browser, Librewolf, etc.).

It applies all necessary compatibility modifications (manifest adjustments, scripting API bypasses, IndexedDB local file storage support, and dynamic origin mapping) without containing or distributing Google's proprietary code.

> [!NOTE]
> **AI Development & Disclaimer:** This project was developed with the assistance of agentic AI coding assistants. Since the code modifications are applied programmatically using regex and heuristics, changes in future upstream extension releases might cause unexpected side effects. Users should use this utility at their own discretion.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

## Files

- `patch.py`: The Python patcher engine (uses standard libraries only).
- `reader_firefox_helper.js`: Custom helper script injected into the custom viewer page (`reader.html`) to support persistent IndexedDB paper storage, sidebar layout, and click interceptions.

## Usage

To patch a downloaded Chrome extension `.zip` file:

```bash
# Extract and patch into a loadable folder
uv run python patch.py path/to/extension.zip ./dist

# Extract and patch directly into a zip file
uv run python patch.py path/to/extension.zip ./patched-firefox-extension.zip
```

## How to Load and Test

1. Open Firefox or Zen Browser.
2. Navigate to `about:debugging#/runtime/this-firefox`.
3. Click **Load Temporary Add-on...**.
4. Select the `manifest.json` from the generated `./dist` directory (or select the built `.zip` file).
5. **Web PDFs:** Open any PDF link on the web (e.g., from Google Scholar or arXiv). It will automatically load in the custom extension reader.
6. **Local PDFs / Library:** Click the extension icon in the toolbar. It will open `reader.html` in a new tab. You can drag and drop PDF files or folders, or click **Browse Files/Folder** to add documents to your persistent local IndexedDB library.

---

## Core Challenges & Adaptations

Porting this extension from Chromium to Firefox-based browsers presents unique technical and security differences. Below are the key engineering challenges and how they are programmatically resolved by the patcher:

### 1. Intercepting PDF Loads
*   **The Problem:** In Chrome, PDF files are loaded inside a generic `application/pdf` page where standard content scripts are allowed to execute. In Firefox, PDFs are handled by the native `PDF.js` viewer, which runs in a privileged security context (`chrome://` or `resource://` schemes) where content scripts matched to `<all_urls>` are strictly blocked.
*   **The Solution:** Instead of waiting for the document to load to inject scripts, the patcher registers a blocking `onHeadersReceived` listener in the background script. It intercepts network responses with `Content-Type: application/pdf` and redirects the navigation (`main_frame` / `sub_frame`) to `reader.html?file=<encoded-url>` before Firefox's built-in PDF viewer can take over.

### 2. Local File Access (`file:///` URLs)
*   **The Problem:** Chrome features a toggle settings switch to "Allow access to file URLs", enabling extensions to read local directories. Firefox provides no such capability, blocking extensions from reading `file:///` URLs directly.
*   **The Solution:** The patcher injects `reader_firefox_helper.js` into the reader workspace. It integrates a persistent local database using the browser's native **IndexedDB** (`ScholarPDFLibrary`). Users can drag-and-drop or select PDF files/folders (recursively mapped via `webkitGetAsEntry`), storing them as persistent files. We map these local files to a mock schema (`http://localpdf/<name>`) and stream them directly from IndexedDB inside the viewer.

### 3. Extension Origin Resolution
*   **The Problem:** Chromium extensions use a static origin structure matching `chrome-extension://` + the Extension ID. Firefox extensions use randomly generated UUIDs (`moz-extension://<random-uuid>`) that differ from the Extension ID. Hardcoded extension origins fail to run or communicate.
*   **The Solution:** The patcher scans all JavaScript files and replaces hardcoded origin identifiers with a dynamic origin lookup: `chrome.runtime.getURL("").slice(0, -1)`.

### 4. Cross-Origin CSRF Blocks
*   **The Problem:** Firefox automatically attaches origin headers (`Origin: moz-extension://<uuid>`) to cross-origin fetches (even `GET` requests). When Google cookies are present, Google's security front-end identifies this cross-origin request and blocks it with `HTTP 403 Forbidden` due to CSRF protection.
*   **The Solution:** The patcher inserts a listener in `background-compiled.js` to strip the `Origin` header and rewrite the `Referer` header to the target domain, and overrides the credentials mode to `"omit"` specifically for `scholar_kp` fetches under Firefox.

### 5. Script Injection Restrictions
*   **The Problem:** Firefox 152+ blocks injecting content scripts into `moz-extension://` domains. Calling `chrome.scripting.executeScript` inside `reader.html` triggers runtime deprecation errors and warnings.
*   **The Solution:** The patcher injects check bypasses in `background-compiled.js` for content-type checks (`Ec`), history restores (`Fc`), reloads (`Gc`), tab dimensions (`Hc`), and referrers (`Ic`), resolving them using background memory cache or tabs API instead of script injections.

### 6. Sandbox Iframe Encoding & Text Rendering (Missing Text Layer)
*   **The Problem:** To satisfy Firefox extension policies and resolve safety warnings ("An iframe which has both allow-scripts and allow-same-origin for its sandbox attribute can remove its sandboxing"), `allow-same-origin` must be removed from the iframe sandbox. However, once removed, the iframe executes under a unique (`null`) origin. In Firefox, if a sandboxed unique-origin iframe is loaded from an HTML template that lacks a `<meta charset="utf-8">` tag, the browser decodes its scripts (`pdf.min.js`, `pdf.worker.min.js`) using default regional fallback encodings (e.g. Windows-1252) instead of UTF-8. This encoding mismatch silently corrupts the minified non-ASCII mapping tables and glyph definitions, causing text layer rendering to fail.
*   **The Solution:** The patcher applies a dual-layer fix:
    1.  Strips `allow-same-origin` from `reader-compiled.js` to enforce proper sandbox isolation and comply with browser policies.
    2.  Injects a `<meta charset="utf-8">` tag into `pdf_loader_iframe.html` before packaging. This forces Firefox to parse the loaded PDF.js scripts in UTF-8, resolving font/CMap corruption and restoring a fully functional selectable text layer.

---

## Detailed File Patches

The `patch.py` utility automatically executes modifications across the following extension files:

*   **[manifest.json](file:///C:/Users/youse/Development/scholar-pdf-patcher/dist/manifest.json)**:
    *   [ ] Injects Gecko-specific settings (`browser_specific_settings`).
    *   [ ] Switches unsupported `"incognito": "split"` to `"spanning"`.
    *   [ ] Modifies extension `permissions` (adds `webRequestBlocking`, removes Chromium `offscreen`).
    *   [ ] Appends `"file:///*"` to `host_permissions`.
    *   [ ] Replaces the background service worker with a scripts array.
    *   [ ] Restricts content scripts to explicit web/file schemas.
    *   [ ] Declares core PDF.js assets in `web_accessible_resources`.
    *   [ ] Removes the Chromium-specific `"sandbox"` and sandbox CSP keys.
*   **[_locales/en/messages.json](file:///C:/Users/youse/Development/scholar-pdf-patcher/dist/_locales/en/messages.json)**:
    *   [ ] Renames menu actions from "Chrome viewer" to "Firefox viewer".
*   **[reader.html](file:///C:/Users/youse/Development/scholar-pdf-patcher/dist/reader.html)**:
    *   [ ] Injects the custom IndexedDB helper script ([reader_firefox_helper.js](file:///C:/Users/youse/Development/scholar-pdf-patcher/reader_firefox_helper.js)).
    *   [ ] Inlines Material-design styles for the library sidebar and drag-and-drop workspace.
*   **[background-compiled.js](file:///C:/Users/youse/Development/scholar-pdf-patcher/dist/background-compiled.js)**:
    *   [ ] Declares the global `bypassedTabs` state cache.
    *   [ ] Resolves dynamic extension origins (`chrome.runtime.getURL`).
    *   [ ] Spoofs headers (`Referer`/`Origin` stripping) and omits credentials to bypass Google CSRF blocks.
    *   [ ] Configures `onHeadersReceived` blocking listener to intercept and redirect PDF navigations.
    *   [ ] Disables instruction popups and redirects scripting API document checks (`Ec`, `Fc`, `Gc`, `Hc`, `Ic`).
    *   [ ] Registers extension action click listener to open the library workspace directly.
*   **[pdf_loader-compiled.js](file:///C:/Users/youse/Development/scholar-pdf-patcher/dist/pdf_loader-compiled.js)**:
    *   [ ] Patches iframe parent `postMessage` targetOrigin resolution.
    *   [ ] Points `GlobalWorkerOptions.workerSrc` directly to `/pdf.worker.min.js`.
*   **[reader-compiled.js](file:///C:/Users/youse/Development/scholar-pdf-patcher/dist/reader-compiled.js)**:
    *   [ ] Strips `allow-same-origin` from the iframe sandbox to satisfy Firefox security policies.
    *   [ ] Guards popover focus event checks to prevent runtime bubble-up crashes.
*   **[pdf_loader_iframe.html](file:///C:/Users/youse/Development/scholar-pdf-patcher/dist/pdf_loader_iframe.html)**:
    *   [ ] Injects `<meta charset="utf-8">` to force correct UTF-8 script decoding.
*   **Script Utilities** (`contentscript-compiled.js`, `historyscript-compiled.js`, `reloadscript-compiled.js`):
    *   [ ] Maps hardcoded Chrome origins to dynamic, variable extension base URLs.

---

## License

This project is licensed under the terms of the GNU General Public License Version 3 (GPLv3). See the [LICENSE](file:///C:/Users/youse/Development/scholar-pdf-patcher/LICENSE) file for the full text.
