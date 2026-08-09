import os
import sys
import re
import json
import shutil
import zipfile
import argparse
from pathlib import Path

# CSS styles to inline in reader.html for the IndexedDB and Library interface
LIBRARY_CSS = """  body.drop-mode {
    background-color: #202124;
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    font-family: Roboto, Arial, sans-serif;
    color: #e8eaed;
  }
  .drop-container {
    background-color: #292a2d;
    border: 2px dashed #5f6368;
    border-radius: 8px;
    padding: 60px 40px;
    width: 440px;
    max-width: 90%;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    transition: all 0.2s ease-in-out;
    cursor: pointer;
  }
  .drop-container:hover, .drop-container.dragover {
    border-color: #8ab4f8;
    background-color: #303134;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  }
  .logo-box {
    margin-bottom: 24px;
    transition: transform 0.2s ease-in-out;
  }
  .logo-box img {
    width: 72px;
    height: 72px;
    object-fit: contain;
  }
  .drop-container:hover .logo-box {
    transform: scale(1.05);
  }
  h2 {
    font-size: 22px;
    font-weight: 500;
    color: #f1f3f4;
    margin: 0 0 8px 0;
    letter-spacing: 0.1px;
  }
  p {
    color: #9aa0a6;
    font-size: 14px;
    margin: 0 0 28px 0;
    line-height: 1.5;
  }
  .browse-btn {
    background-color: #8ab4f8;
    border: none;
    color: #202124;
    padding: 10px 24px;
    border-radius: 4px;
    font-weight: 500;
    font-size: 14px;
    transition: background-color 0.2s ease, color 0.2s ease;
    cursor: pointer;
  }
  .browse-btn:hover {
    background-color: #aecbfa;
  }
  #browseFolderBtn {
    background-color: #3c4043;
    color: #e8eaed;
    border: 1px solid #5f6368;
  }
  #browseFolderBtn:hover {
    background-color: #3c4043;
    color: #8ab4f8;
    border-color: #8ab4f8;
  }
  #fileInput {
    display: none;
  }

  /* Sidebar and layout styles */
  .app-layout {
    display: flex;
    flex-direction: row;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    background-color: #202124;
  }
  .gsr-root-wrap {
    flex: 1;
    height: 100%;
    position: relative;
    overflow: hidden;
  }
  
  .library-sidebar {
    width: 280px;
    min-width: 280px;
    max-width: 280px;
    height: 100%;
    background-color: #202124;
    border-right: 1px solid #3c4043;
    display: flex;
    flex-direction: column;
    transition: width 0.2s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease;
    overflow: hidden;
    box-sizing: border-box;
    z-index: 10;
  }
  .library-sidebar.collapsed {
    width: 0px;
    min-width: 0px;
    max-width: 0px;
    border-right: none;
    opacity: 0;
    pointer-events: none;
  }

  .sidebar-header {
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #3c4043;
  }
  .sidebar-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 500;
    color: #f1f3f4;
  }
  .add-paper-btn {
    background: none;
    border: none;
    color: #8ab4f8;
    font-size: 24px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    transition: background-color 0.2s;
  }
  .add-paper-btn:hover {
    background-color: #303134;
  }

  .search-box {
    padding: 12px 16px;
    border-bottom: 1px solid #3c4043;
  }
  .search-box input {
    width: 100%;
    padding: 8px 12px;
    background-color: #2d2e30;
    border: 1px solid #5f6368;
    border-radius: 4px;
    color: #e8eaed;
    font-size: 14px;
    box-sizing: border-box;
  }
  .search-box input:focus {
    border-color: #8ab4f8;
    outline: none;
  }

  .paper-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }
  .paper-list::-webkit-scrollbar {
    width: 6px;
  }
  .paper-list::-webkit-scrollbar-track {
    background: transparent;
  }
  .paper-list::-webkit-scrollbar-thumb {
    background-color: #5f6368;
    border-radius: 3px;
  }

  .paper-item {
    display: flex;
    align-items: center;
    padding: 10px 16px;
    cursor: pointer;
    transition: background-color 0.2s;
    user-select: none;
    gap: 12px;
  }
  .paper-item:hover {
    background-color: #303134;
  }
  .paper-item.active {
    background-color: rgba(138, 180, 248, 0.12);
  }
  .paper-icon {
    display: flex;
    align-items: center;
    color: #9aa0a6;
    flex-shrink: 0;
  }
  .paper-item.active .paper-icon {
    color: #8ab4f8;
  }
  .paper-icon svg {
    width: 20px;
    height: 20px;
    fill: currentColor;
  }
  .paper-title {
    flex: 1;
    font-size: 14px;
    color: #e8eaed;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .paper-item.active .paper-title {
    color: #8ab4f8;
    font-weight: 500;
  }
  .delete-btn {
    background: none;
    border: none;
    color: #9aa0a6;
    font-size: 18px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s, color 0.2s;
    padding: 0 4px;
    line-height: 1;
  }
  .paper-item:hover .delete-btn {
    opacity: 1;
  }
  .delete-btn:hover {
    color: #f28b82;
  }

  .sidebar-footer {
    padding: 12px 16px;
    border-top: 1px solid #3c4043;
    display: flex;
    justify-content: center;
  }
  .clear-lib-btn {
    background-color: transparent;
    border: 1px solid #5f6368;
    color: #9aa0a6;
    padding: 6px 16px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    width: 100%;
  }
  .clear-lib-btn:hover {
    background-color: rgba(242, 139, 130, 0.08);
    border-color: #f28b82;
    color: #f28b82;
  }

  .empty-list {
    padding: 24px;
    text-align: center;
    color: #9aa0a6;
    font-size: 14px;
  }

  /* Dropdown menu for Add Paper */
  .add-paper-dropdown {
    position: absolute;
    background-color: #2d2e30;
    border: 1px solid #3c4043;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    z-index: 1001;
    display: none;
    flex-direction: column;
    padding: 4px 0;
    min-width: 150px;
  }
  .add-paper-dropdown.show {
    display: flex;
  }
  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    color: #e8eaed;
    font-size: 13px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  .dropdown-item:hover {
    background-color: #3c4043;
  }
  .dropdown-item svg {
    width: 16px;
    height: 16px;
    fill: #9aa0a6;
  }
  .dropdown-item:hover svg {
    fill: #8ab4f8;
  }

  /* Floating toggle button */
  .sidebar-toggle {
    position: fixed;
    bottom: 24px;
    left: 304px;
    z-index: 1000;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background-color: #2d2e30;
    border: 1px solid #3c4043;
    color: #e8eaed;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: left 0.2s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.2s, transform 0.2s;
  }
  .sidebar-toggle:hover {
    background-color: #3c4043;
    color: #8ab4f8;
    transform: scale(1.05);
  }
  .app-layout:has(.library-sidebar.collapsed) .sidebar-toggle {
    left: 24px;
  }
  .sidebar-toggle svg {
    width: 20px;
    height: 20px;
    fill: currentColor;
  }

  /* Placeholder dropzone in layout */
  .gsr-root-wrap:has(.placeholder-drop) {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #202124;
  }
  .drop-container.placeholder-drop {
    box-shadow: none;
    border-color: #3c4043;
    background-color: #202124;
  }
  .drop-container.placeholder-drop:hover, .drop-container.placeholder-drop.dragover {
    border-color: #8ab4f8;
    background-color: #292a2d;
  }"""

def patch_manifest(manifest_path: Path):
    print(f"[*] Patching manifest.json...")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Clean up unused fields
    manifest.pop("minimum_chrome_version", None)
    manifest.pop("update_url", None)
    
    # In Firefox MV3, incognito "split" is unsupported; we use "spanning" instead
    if manifest.get("incognito") == "split":
        manifest["incognito"] = "spanning"

    # 2. Add Gecko Specific Settings
    manifest["browser_specific_settings"] = {
        "gecko": {
            "id": "scholar-pdf-reader-port@addon",
            "strict_min_version": "109.0",
            "data_collection_permissions": {
                "required": ["none"]
            }
        }
    }

    # 3. Modify Permissions
    perms = manifest.get("permissions", [])
    if "offscreen" in perms:
        perms.remove("offscreen")
    if "webRequestBlocking" not in perms:
        perms.append("webRequestBlocking")
    manifest["permissions"] = perms

    # 4. Modify Host Permissions
    host_perms = manifest.get("host_permissions", [])
    if "file:///*" not in host_perms:
        host_perms.append("file:///*")
    manifest["host_permissions"] = host_perms

    # 5. Modify Background Service Worker to Firefox Scripts
    bg = manifest.get("background", {})
    if "service_worker" in bg:
        service_worker = bg.pop("service_worker")
        bg["scripts"] = [service_worker]
    manifest["background"] = bg

    # 6. Modify Content Scripts matches (exclude internal moz-extension scheme)
    for cs in manifest.get("content_scripts", []):
        matches = cs.get("matches", [])
        if "<all_urls>" in matches:
            new_matches = []
            for m in matches:
                if m == "<all_urls>":
                    new_matches.extend(["http://*/*", "https://*/*", "file:///*"])
                else:
                    new_matches.append(m)
            cs["matches"] = new_matches

    # 7. Remove sandboxed pages declaration (sandboxed pages cannot receive message channel fetches easily on Firefox)
    manifest.pop("sandbox", None)

    # 8. Clean up Sandbox CSP
    csp = manifest.get("content_security_policy", {})
    csp.pop("sandbox", None)
    manifest["content_security_policy"] = csp

    # 9. Modify web accessible resources to expose pdf.js libraries
    war = manifest.get("web_accessible_resources", [])
    found = False
    for item in war:
        if "resources" in item:
            resources = item["resources"]
            if "reader.html" in resources:
                for res in ["pdf.min.js", "pdf.worker.min.js", "pdf_loader-compiled.js", "bcmaps/*"]:
                    if res not in resources:
                        resources.append(res)
                found = True
    if not found:
        war.append({
            "resources": ["reader.html", "pdf_loader_iframe.html", "pdf.min.js", "pdf.worker.min.js", "pdf_loader-compiled.js", "bcmaps/*"],
            "matches": ["<all_urls>"]
        })
    manifest["web_accessible_resources"] = war

    # 10. Update Author format if necessary
    if isinstance(manifest.get("author"), dict):
        manifest["author"] = manifest["author"].get("email", "scholar-chrome-extensions@google.com")

    # Save manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("[+] manifest.json patched successfully!")

def patch_locales(locales_path: Path):
    print(f"[*] Patching locales message keys...")
    if not locales_path.exists():
        print(f"[-] Locales path {locales_path} not found, skipping.")
        return

    with open(locales_path, "r", encoding="utf-8") as f:
        locales = json.load(f)

    if "1627" in locales and "message" in locales["1627"]:
        locales["1627"]["message"] = locales["1627"]["message"].replace("Chrome viewer", "Firefox viewer")
    if "1723" in locales and "message" in locales["1723"]:
        locales["1723"]["message"] = locales["1723"]["message"].replace("Chrome viewer", "Firefox viewer")

    with open(locales_path, "w", encoding="utf-8") as f:
        json.dump(locales, f, indent=2)
    print("[+] Locales patched successfully!")

def patch_reader_html(reader_html_path: Path):
    print(f"[*] Patching reader.html...")
    with open(reader_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Replace the reader-compiled.js script tag with firefox helper script tag and CSS inlining
    target_script = '<script src="/reader-compiled.js" defer></script>'
    replacement = (
        f'<script src="/reader_firefox_helper.js" defer></script>\n'
        f' <style>\n{LIBRARY_CSS}\n </style>'
    )
    if target_script in html:
        html = html.replace(target_script, replacement)
    else:
        # fallback regex if formatting differs
        html = re.sub(
            r'<script\s+src=["\']/reader-compiled\.js["\']\s*defer\s*>\s*</script>',
            replacement,
            html
        )

    with open(reader_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("[+] reader.html patched successfully!")

def deminify_js_files(target_dir: Path):
    print(f"[*] Deminifying and formatting JavaScript files...")
    try:
        import jsbeautifier
    except ImportError:
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "jsbeautifier"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import jsbeautifier
        except Exception:
            jsbeautifier = None

    if jsbeautifier:
        opts = jsbeautifier.default_options()
        opts.indent_size = 2
        opts.keep_array_indentation = True
        opts.break_chained_methods = False

        for js_file in target_dir.glob("*.js"):
            try:
                raw = js_file.read_text(encoding="utf-8", errors="ignore")
                formatted = jsbeautifier.beautify(raw, opts)
                js_file.write_text(formatted, encoding="utf-8")
            except Exception as e:
                print(f"    - Warning: Failed to beautify {js_file.name}: {e}")
        print("[+] JavaScript files deminified and formatted successfully.")
    else:
        print("    - Notice: jsbeautifier not found. Proceeding with raw extracted JavaScript.")


def patch_background_js(bg_js_path: Path):
    print(f"[*] Patching background-compiled.js...")
    with open(bg_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace dynamic origin schema
    # Search for "chrome-extension://" + chrome.runtime.id (handles variations in spaces/quotes)
    content, count1 = re.subn(
        r'["\']chrome-extension://["\']\s*\+\s*chrome\.runtime\.id',
        'chrome.runtime.getURL("").slice(0,-1)',
        content
    )
    print(f"    - Origin scheme replacements: {count1}")

    # 2. Add chrome-extension / moz-extension initiator startsWith support in headers interceptor
    # Search for: (a.initiator||"").startsWith("chrome-extension://")
    content, count = re.subn(
        r'([a-zA-Z0-9_$]+)\.initiator\s*\|\|\s*["\']["\']\s*\)\s*\.startsWith\(\s*["\']chrome-extension://["\']\s*\)',
        r'(\1.initiator||"").startsWith("chrome-extension://")||(\1.initiator||"").startsWith("moz-extension://")',
        content
    )
    print(f"    - Initiator scheme checks patched: {count}")

    # 3. Extract the name of the 'Y' tab storage helper function
    y_match = re.search(
        r'onBeforeSendHeaders\.addListener\([^)]*\)\s*=>\s*\{\s*if\([^)]*\)\s*\{\s*var\s+[a-zA-Z0-9_$]+\s*=\s*[a-zA-Z0-9_$]+\([^)]*,\s*"referer"\s*\)\s*,\s*[a-zA-Z0-9_$]+\s*=\s*[a-zA-Z0-9_$]+\.url\s*;\s*([a-zA-Z0-9_$]+)\(',
        content
    )
    y_func_name = y_match.group(1) if y_match else "Y"
    print(f"    - Found tab cache function name: '{y_func_name}'")

    # 4. Inject bypassedTabs declaration globally at the start of the script wrapper
    content = re.sub(r'\(function\s*\(\s*\)\s*\{', '(function(){var bypassedTabs = new Set();', content, count=1)
    print("    - bypassedTabs cache Set injected globally.")

    # 5. Fix onBeforeSendHeaders listener signature compatibility for Firefox
    obs_pattern = r'\}\s*,\s*\{\s*urls\s*:\s*\[\s*["\']<all_urls>["\']\s*\]\s*\}\s*,\s*\[\s*["\']requestHeaders["\']\s*,\s*["\']extraHeaders["\']\s*\]\s*\)\s*;'
    content, obs_count = re.subn(
        obs_pattern,
        '}, {urls: ["<all_urls>"]}, typeof browser !== "undefined" ? ["requestHeaders"] : ["requestHeaders", "extraHeaders"]);',
        content,
        count=1
    )
    print(f"    - onBeforeSendHeaders listener signature updated: {obs_count} replacements.")

    # 6. Inject the google.com header strip blocking listener for Firefox
    firefox_header_listener = """if (typeof browser !== "undefined") {
  chrome.webRequest.onBeforeSendHeaders.addListener(
    a => {
      let headers = a.requestHeaders;
      let modified = false;
      let targetOrigin = "";
      try {
        let urlObj = new URL(a.url);
        targetOrigin = urlObj.origin + "/";
      } catch (e) {}
      for (let i = 0; i < headers.length; i++) {
        let name = headers[i].name.toLowerCase();
        let value = headers[i].value || "";
        if (name === "origin" && value.startsWith("moz-extension://")) {
          headers.splice(i, 1);
          i--;
          modified = true;
        } else if (name === "referer" && value.startsWith("moz-extension://")) {
          if (targetOrigin) {
            headers[i].value = targetOrigin;
            modified = true;
          }
        }
      }
      if (modified) return { requestHeaders: headers };
    },
    { urls: ["*://*.google.com/*"] },
    ["blocking", "requestHeaders"]
  );
}"""
    # Inject it right after the onBeforeSendHeaders listener registration
    search_pos = content.find('typeof browser !== "undefined" ? ["requestHeaders"] : ["requestHeaders", "extraHeaders"]);')
    if search_pos != -1:
        insert_idx = search_pos + len('typeof browser !== "undefined" ? ["requestHeaders"] : ["requestHeaders", "extraHeaders"]);')
        content = content[:insert_idx] + "\n" + firefox_header_listener + content[insert_idx:]
        print("    - Firefox google.com Origin/Referer header cleaning listener injected.")
    else:
        # Fallback search without space
        search_pos = content.find('typeof browser !== "undefined" ? ["requestHeaders"] : ["requestHeaders","extraHeaders"]);')
        if search_pos != -1:
            insert_idx = search_pos + len('typeof browser !== "undefined" ? ["requestHeaders"] : ["requestHeaders","extraHeaders"]);')
            content = content[:insert_idx] + "\n" + firefox_header_listener + content[insert_idx:]
            print("    - Firefox google.com Origin/Referer header cleaning listener injected.")
        else:
            print("    - WARNING: Could not find onBeforeSendHeaders registration to inject Firefox header cleaner.")

    # 7. Inject the onHeadersReceived redirect listener logic
    # Find: chrome.webRequest.onHeadersReceived.addListener(a=>{if(a.tabId>=0&&a.type==="main_frame"){
    redirect_injected_logic = """  if (typeof browser !== "undefined" && a.tabId >= 0 && (a.type === "main_frame" || a.type === "sub_frame")) {
    const contentType = uc(a.responseHeaders, "content-type").split(";", 1)[0].trim().toLowerCase();
    console.log("[ScholarPDF] Intercepted request:", a.url, "ContentType:", contentType, "Type:", a.type);
    if (contentType === "application/pdf") {
      if (bypassedTabs.has(a.tabId)) {
        console.log("[ScholarPDF] Redirect bypassed for tabId:", a.tabId);
        bypassedTabs.delete(a.tabId);
        return;
      }
      const dynamicOrigin = chrome.runtime.getURL("").slice(0, -1);
      if (!(a.initiator && a.initiator.startsWith(dynamicOrigin)) && !a.url.startsWith(dynamicOrigin)) {
        try {
          const parsedUrl = new URL(a.url);
          if (parsedUrl.searchParams.get("bypass") === "1" || parsedUrl.searchParams.get("gsr") === "0") {
            console.log("[ScholarPDF] Redirect bypassed by URL parameters:", a.url);
            return;
          }
        } catch (err) {}
        const redirectUrl = chrome.runtime.getURL("reader.html") + "?file=" + encodeURIComponent(a.url);
        console.log("[ScholarPDF] Redirecting to viewer:", redirectUrl);
        return { redirectUrl: redirectUrl };
      }
    }
  }
"""
    on_headers_received_pattern = r'chrome\.webRequest\.onHeadersReceived\.addListener\(\s*([a-zA-Z0-9_$]+)\s*=>\s*\{\s*if\s*\(\s*\1\.tabId\s*>=\s*0\s*&&\s*\1\.type\s*===\s*"main_frame"\s*\)\s*\{\s*var'
    match = re.search(on_headers_received_pattern, content)
    if match:
        var_name = match.group(1)
        localized_redirect = redirect_injected_logic.replace("a.", f"{var_name}.")
        replacement = f'chrome.webRequest.onHeadersReceived.addListener({var_name}=>{{\n{localized_redirect}  if({var_name}.tabId>=0&&{var_name}.type==="main_frame"){{var'
        content = re.sub(on_headers_received_pattern, replacement, content, count=1)
        print("    - Firefox PDF content-type redirect interceptor injected into onHeadersReceived listener.")
    else:
        print("    - WARNING: Could not find onHeadersReceived listener pattern to inject redirect logic.")

    # 8. Update onHeadersReceived signature for Firefox compatibility
    # Handles potential newlines and whitespaces in the minified output options
    signature_pattern = r'\}\s*,\s*\{\s*urls\s*:\s*\[\s*["\']<all_urls>["\']\s*\]\s*\}\s*,\s*\[\s*["\']responseHeaders["\']\s*\]\s*\)\s*;'
    content, count_sig = re.subn(
        signature_pattern,
        '}, {urls: ["<all_urls>"]}, typeof browser !== "undefined" ? ["responseHeaders", "blocking"] : ["responseHeaders"]);',
        content
    )
    print(f"    - onHeadersReceived listener signature updated: {count_sig} replacements.")

    # 9. Wrap the chrome.extension.isAllowedFileSchemeAccess and Ac(a) check block
    # Matches: function Ac(a){...} chrome.extension.isAllowedFileSchemeAccess(...)
    # and wraps it in a conditional Chromium check.
    is_allowed_pattern = r'(function\s+([a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{\s*chrome\.windows\.getCurrent.*?chrome\.extension\.isAllowedFileSchemeAccess\s*\(function\s*\([^)]*\)\s*\{.*?\.[pP][dD][fF]"\s*\}\s*\]\s*\}\s*\)\s*\}\s*\)\s*;?)'
    match_allowed = re.search(is_allowed_pattern, content, re.DOTALL)
    if match_allowed:
        full_block = match_allowed.group(1)
        content = content.replace(full_block, f'if (typeof browser === "undefined") {{\n{full_block}\n}}')
        print("    - AllowedFileSchemeAccess instruction popups disabled for Firefox.")
    else:
        print("    - WARNING: Could not find AllowedFileSchemeAccess popup block to disable.")

    # 10. Patch fetch builder (Bc) to strip credentials Mode for scholar_kp requests
    # matches: function Bc(a){var b={credentials:"include"};switch(a.method){
    # and injects: if(typeof browser!=="undefined"&&a.url&&a.url.includes("scholar_kp")){b.credentials="omit"}
    fetch_builder_pattern = r'function\s+([a-zA-Z0-9_$]+)\s*\(\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*var\s+([a-zA-Z0-9_$]+)\s*=\s*\{\s*credentials\s*:\s*"include"\s*\}\s*;\s*switch\s*\(\s*\2\.method\s*\)'
    match_fetch = re.search(fetch_builder_pattern, content)
    if match_fetch:
        func_name = match_fetch.group(1)
        arg_name = match_fetch.group(2)
        var_name = match_fetch.group(3)
        replacement = f'function {func_name}({arg_name}){{var {var_name}={{credentials:"include"}};if(typeof browser!=="undefined"&&{arg_name}.url&&{arg_name}.url.includes("scholar_kp")){{{var_name}.credentials="omit"}}switch({arg_name}.method)'
        content = re.sub(fetch_builder_pattern, replacement, content, count=1)
        print("    - scholar_kp fetch credentials mode set to 'omit' for Firefox.")
    else:
        print("    - WARNING: Could not find credentials options builder to inject cookie omission block.")

    # 11. Bypass scripting API document content-type check wrapper function (Ec)
    # matches async function Ec(a,b){var c=await chrome.webNavigation.getAllFrames...
    # prepends: if(typeof browser!=="undefined")return Promise.resolve(!0);
    ec_pattern = r'async\s+function\s+([a-zA-Z0-9_$]+)\s*\(\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*(var\s+[a-zA-Z0-9_$]+\s*=\s*await\s+chrome\.webNavigation\.getAllFrames)'
    match_ec = re.search(ec_pattern, content)
    if match_ec:
        func_name = match_ec.group(1)
        arg1 = match_ec.group(2)
        arg2 = match_ec.group(3)
        rem_code = match_ec.group(4)
        replacement = f'async function {func_name}({arg1},{arg2}){{if(typeof browser!=="undefined")return Promise.resolve(!0);{rem_code}'
        content = re.sub(ec_pattern, replacement, content, count=1)
        print("    - scripting.executeScript content-type check (Ec) bypassed on Firefox.")
    else:
        print("    - WARNING: Could not find Ec content-type check function to bypass.")

    # 12. Bypass history recovering script injection (Fc)
    # matches function Fc(a,b,c,d){...} and returns historyscript-compiled.js execution
    # prepends: if(typeof browser!=="undefined")return Promise.resolve(!1);
    fc_pattern = r'function\s+([a-zA-Z0-9_$]+)\s*\(\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*(?=[\s\S]*?historyscript-compiled\.js)'
    match_fc = re.search(fc_pattern, content)
    if match_fc:
        func_name = match_fc.group(1)
        arg1 = match_fc.group(2)
        arg2 = match_fc.group(3)
        arg3 = match_fc.group(4)
        arg4 = match_fc.group(5)
        replacement = f'function {func_name}({arg1},{arg2},{arg3},{arg4}){{if(typeof browser!=="undefined")return Promise.resolve(!1);'
        content = re.sub(fc_pattern, replacement, content, count=1)
        print("    - history script execution (Fc) bypassed on Firefox.")
    else:
        print("    - WARNING: Could not find Fc history script function to bypass.")

    # 13. Bypass reload script injection (Gc)
    # matches async function Gc(a){...} reloading tab via executeScript with reloadscript-compiled.js
    # prepends: if(typeof browser!=="undefined")return Promise.resolve();
    gc_pattern = r'async\s+function\s+([a-zA-Z0-9_$]+)\s*\(\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*(?=[\s\S]*?reloadscript-compiled\.js)'
    match_gc = re.search(gc_pattern, content)
    if match_gc:
        func_name = match_gc.group(1)
        arg_name = match_gc.group(2)
        replacement = f'async function {func_name}({arg_name}){{if(typeof browser!=="undefined")return Promise.resolve();'
        content = re.sub(gc_pattern, replacement, content, count=1)
        print("    - reload script execution (Gc) bypassed on Firefox.")
    else:
        print("    - WARNING: Could not find Gc reload script function to bypass.")

    # 14. Bypass window dimension check script injection (Hc)
    # matches function Hc(a,b,c,d){... return executeScript window.innerWidth...}
    # replaces with tab.width lookup on Firefox
    hc_pattern = r'function\s+([a-zA-Z0-9_$]+)\s*\(\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*(?=[\s\S]*?window\.innerWidth)'
    match_hc = re.search(hc_pattern, content)
    if match_hc:
        func_name = match_hc.group(1)
        arg1 = match_hc.group(2)
        arg2 = match_hc.group(3)
        arg3 = match_hc.group(4)
        arg4 = match_hc.group(5)
        replacement = f'function {func_name}({arg1},{arg2},{arg3},{arg4}){{if(typeof browser!=="undefined"){{return chrome.tabs.get({arg3}).then(tab=>({{width:tab.width||1024,height:tab.height||768}})).catch(()=>({{width:1024,height:768}}))}}'
        content = re.sub(hc_pattern, replacement, content, count=1)
        print("    - window dimensions check script execution (Hc) replaced with tab object query.")
    else:
        print("    - WARNING: Could not find Hc window dimensions function to patch.")

    # 15. Patch referrer check (Ic) to read referrer from background memory cache
    # matches: function Ic(a){return chrome.scripting.executeScript(document.referrer)}
    # replaces it with lookup inside our 'Y' cache function
    ic_pattern = r'function\s+([a-zA-Z0-9_$]+)\s*\(\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*return\s+chrome\.scripting\.executeScript\(\{\s*target\s*:\s*\{\s*tabId\s*:\s*\2\s*\}\s*,\s*func\s*:\s*function\(\)\s*\{\s*return\s+document\.referrer\s*\}\s*\}\)\.then\(\s*[a-zA-Z0-9_$]+\s*=>\s*([a-zA-Z0-9_$]+)\.test'
    match_ic = re.search(ic_pattern, content)
    if match_ic:
        func_name = match_ic.group(1)
        arg_name = match_ic.group(2)
        regex_var = match_ic.group(3)
        target_body = f'function {func_name}({arg_name}){{'
        replacement_body = f'function {func_name}({arg_name}){{if(typeof browser!=="undefined"){{try{{const stored={y_func_name}({arg_name},0);if(stored&&stored.hb&&stored.hb.referrer){{return Promise.resolve({regex_var}.test((new URL(stored.hb.referrer)).host))}}}}catch(e){{}}return Promise.resolve(!1)}}'
        content = content.replace(target_body, replacement_body, 1)
        print("    - referrer lookup script execution (Ic) replaced with tab navigator background history cache.")
    else:
        print("    - WARNING: Could not find Ic referrer check function to patch.")

    # 16. Patch chrome.runtime.onConnect listener to bypass yc parent frame lookup if reader loaded directly
    # matches the case "getUrl": yc(b.tab.id, b.frameId).then(...) block
    get_url_pattern = (
        r'case\s*"getUrl"\s*:\s*([a-zA-Z0-9_$]+)\(\s*([a-zA-Z0-9_$]+)\.tab\.id\s*,\s*\2\.frameId\s*\)\.then\(\s*([a-zA-Z0-9_$]+)\s*=>\s*\{\s*'
        r'var\s+([a-zA-Z0-9_$]+)\s*=\s*\3\.J\s*,\s*([a-zA-Z0-9_$]+)\s*=\s*\3\.Ia\s*,\s*([a-zA-Z0-9_$]+)\s*=\s*\3\.Ja\s*,\s*([a-zA-Z0-9_$]+)\s*=\s*\3\.parentFrameId\s*;\s*'
        r'\4\s*\|\|\s*console\.error\("[^"]+",\s*\2\)\s*;\s*'
        r'var\s+([a-zA-Z0-9_$]+)\s*=\s*([a-zA-Z0-9_$]+)\(\s*([a-zA-Z0-9_$]+)\s*\)\s*;\s*'
        r'([a-zA-Z0-9_$]+)\(\s*\4\s*,\s*\10\s*\)\.then\(\s*([a-zA-Z0-9_$]+)\s*=>\s*\{\s*'
        r'var\s+([a-zA-Z0-9_$]+)\s*=\s*([a-zA-Z0-9_$]+)\(\s*\4\s*,\s*\5\s*,\s*\10\s*,\s*\12\s*\)\s*,\s*([a-zA-Z0-9_$]+)\s*=\s*([a-zA-Z0-9_$]+)\(\s*\4\s*,\s*\5\s*,\s*\10\s*,\s*\12\s*\)\s*,\s*([a-zA-Z0-9_$]+)\s*=\s*([a-zA-Z0-9_$]+)\(\s*\10\s*\)\s*;\s*'
        r'Promise\.all\(\[\s*\13\s*,\s*\15\s*,\s*\8\s*,\s*\17\s*\]\)\.then\(\(\[\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*\]\)\s*=>\s*\{\s*'
        r'([a-zA-Z0-9_$]+)\s*&&\s*([a-zA-Z0-9_$]+)\.postMessage\(\{\s*pdfUrl:\s*\4\s*,\s*topWindowUrlBeforeRedirects:\s*\6\s*\|\|\s*\5\s*,\s*isScholarTopReferrer:\s*\21\s*,\s*isHistoryOnTopWindow:\s*\19\s*,\s*shouldShowSignedInFeatures:\s*\12\s*,\s*topWindowWidth:\s*\20\.width\s*,\s*topWindowHeight:\s*\20\.height\s*,\s*parentFrameId:\s*\7\s*\}\)\s*\}\)\s*\}\)\s*\}\s*,\s*[a-zA-Z0-9_$]+\s*=>\s*\{\s*console\.error\([^)]*\)\s*\}\)'
    )
    match_get_url = re.search(get_url_pattern, content)
    if match_get_url:
        yc_helper = match_get_url.group(1)
        sender_var = match_get_url.group(2)
        res_var = match_get_url.group(3)
        pdf_url_var = match_get_url.group(4)
        top_url_var = match_get_url.group(5)
        final_url_var = match_get_url.group(6)
        parent_frame_var = match_get_url.group(7)
        ref_check_res_var = match_get_url.group(8)
        ic_func = match_get_url.group(9)
        tab_id_var = match_get_url.group(10)
        ec_func = match_get_url.group(11)
        show_signed_var = match_get_url.group(12)
        history_check_var = match_get_url.group(13)
        fc_func = match_get_url.group(14)
        dims_check_var = match_get_url.group(15)
        hc_func = match_get_url.group(16)
        reload_check_var = match_get_url.group(17)
        gc_func = match_get_url.group(18)
        destruct1 = match_get_url.group(19)
        destruct2 = match_get_url.group(20)
        destruct3 = match_get_url.group(21)
        alive_var = match_get_url.group(22)
        port_var = match_get_url.group(23)

        yc_bypass_replacement = f"""case "getUrl":
          let pdfUrlFromQuery = "";
          try {{
            if ({sender_var}.url) {{
              const urlObj = new URL({sender_var}.url);
              pdfUrlFromQuery = urlObj.searchParams.get("file") || "";
            }}
          }} catch (err) {{}}

          const handleGetUrl = ({pdf_url_var},{top_url_var},{final_url_var},{parent_frame_var})=>{{
            if(!{pdf_url_var}){{
              console.error("Failed to get URL to load",{sender_var});
              return;
            }}
            var {ref_check_res_var}={ic_func}({tab_id_var});
            {ec_func}({pdf_url_var},{tab_id_var}).then({show_signed_var}=>{{
              var {history_check_var}={fc_func}({pdf_url_var},{top_url_var},{tab_id_var},{show_signed_var}),{dims_check_var}={hc_func}({pdf_url_var},{top_url_var},{tab_id_var},{show_signed_var}),{reload_check_var}={gc_func}({tab_id_var});
              Promise.all([{history_check_var},{dims_check_var},{ref_check_res_var},{reload_check_var}]).then(([{destruct1},{destruct2},{destruct3}])=>{{
                {alive_var}&&{port_var}.postMessage({{
                  pdfUrl:{pdf_url_var},
                  topWindowUrlBeforeRedirects:{final_url_var}||{top_url_var},
                  isScholarTopReferrer:{destruct3},
                  isHistoryOnTopWindow:{destruct1},
                  shouldShowSignedInFeatures:{show_signed_var},
                  topWindowWidth:{destruct2}.width,
                  topWindowHeight:{destruct2}.height,
                  parentFrameId:{parent_frame_var}
                }})
              }})
            }})
          }};

          if (pdfUrlFromQuery) {{
            handleGetUrl(pdfUrlFromQuery, pdfUrlFromQuery, pdfUrlFromQuery, 0);
          }} else {{
            {yc_helper}({sender_var}.tab.id,{sender_var}.frameId).then({res_var}=>{{
              handleGetUrl({res_var}.J,{res_var}.Ia,{res_var}.Ja,{res_var}.parentFrameId);
            }},{res_var}=>{{
              console.error("Failed to get URL to load, reason:",{res_var},{sender_var})
            }});
          }}"""
        content = re.sub(get_url_pattern, yc_bypass_replacement, content, count=1)
        print("    - getUrl connecting port message listener patched to support direct queries.")
    else:
        print("    - WARNING: Could not find getUrl connection handler in onConnect to patch.")

    # 17. Wrap the offscreen document creation check (Jc)
    # Matches: async function Jc(){...}
    # Adds chrome.offscreen existence checks
    offscreen_pattern = r'async\s+function\s+([a-zA-Z0-9_$]+)\(\)\s*\{\s*(var\s+[a-zA-Z0-9_$]+\s*=\s*chrome\.runtime\.getURL\(\s*"offscreen\.html"\s*\))'
    match_offscreen = re.search(offscreen_pattern, content)
    if match_offscreen:
        func_name = match_offscreen.group(1)
        rem_code = match_offscreen.group(2)
        replacement = f'async function {func_name}(){{if (typeof chrome === "undefined" || !chrome.offscreen) return Promise.resolve();{rem_code}'
        content = re.sub(offscreen_pattern, replacement, content, count=1)
        print("    - Jc offscreen document creator guarded for Firefox.")
    else:
        print("    - WARNING: Could not find Jc offscreen document function to patch.")

    # 18. Wrap the clipboard copy implementation (Kc) with local clipboard fallback
    # Matches: async function Kc(a,b,c){await Jc();chrome.runtime.sendMessage(...)}
    # Adds document.execCommand fallback
    kc_pattern = r'async\s+function\s+([a-zA-Z0-9_$]+)\(\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*await\s+([a-zA-Z0-9_$]+)\(\)\s*;\s*chrome\.runtime\.sendMessage\(\s*\{\s*type\s*:\s*"offscreen-copy"\s*,\s*timestamp\s*:\s*\2\s*,\s*plainText\s*:\s*\3\s*,\s*htmlText\s*:\s*\4\s*\}\)\s*\}'
    match_kc = re.search(kc_pattern, content)
    if match_kc:
        func_name = match_kc.group(1)
        arg1 = match_kc.group(2)
        arg2 = match_kc.group(3)
        arg3 = match_kc.group(4)
        jc_func_name = match_kc.group(5)
        replacement = f"""async function {func_name}({arg1},{arg2},{arg3}){{
  if (typeof chrome !== "undefined" && chrome.offscreen) {{
    await {jc_func_name}();
    chrome.runtime.sendMessage({{type:"offscreen-copy",timestamp:{arg1},plainText:{arg2},htmlText:{arg3}}});
  }} else {{
    try {{
      const listener = e => {{
        e.preventDefault();
        e.clipboardData.setData("text/plain", {arg2});
        if ({arg3} !== undefined) {{
          e.clipboardData.setData("text/html", {arg3});
        }}
      }};
      document.addEventListener("copy", listener);
      document.execCommand("copy");
      document.removeEventListener("copy", listener);
    }} catch (err) {{
      console.error("Fallback copy failed:", err);
    }}
  }}
}}"""
        content = re.sub(kc_pattern, replacement, content, count=1)
        print("    - Kc clipboard copy background task patched with DOM document.execCommand copy fallback.")
    else:
        print("    - WARNING: Could not find Kc clipboard copy function to patch.")

    # 19. Patch chrome.runtime.onMessage listener for bypass-tab-redirect support and signature change
    # Matches: chrome.runtime.onMessage.addListener((a,b)=>{if(a&&b.origin===sc&&typeof a==="object")if(b=a.type,b==="background-copy")
    # injects bypass-tab-redirect set mapping
    on_msg_pattern = r'chrome\.runtime\.onMessage\.addListener\(\s*\(\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*\)\s*=>\s*\{\s*if\s*\(\s*\1\s*&&\s*\2\.origin\s*===\s*([a-zA-Z0-9_$]+)\s*&&\s*typeof\s+\1\s*===\s*"object"\s*\)\s*if\s*\(\s*\2\s*=\s*\1\.type\s*,\s*\2\s*===\s*"background-copy"\s*\)'
    match_on_msg = re.search(on_msg_pattern, content)
    if match_on_msg:
        msg_arg = match_on_msg.group(1)
        sender_arg = match_on_msg.group(2)
        origin_var = match_on_msg.group(3)
        replacement = f'chrome.runtime.onMessage.addListener(({msg_arg},sender)=>{{let {sender_arg};if({msg_arg}&&sender.origin==={origin_var}&&typeof {msg_arg}==="object")if({msg_arg}.type==="bypass-tab-redirect"){{if(sender.tab){{bypassedTabs.add(sender.tab.id);setTimeout(()=>bypassedTabs.delete(sender.tab.id),3000);}}}}else if({sender_arg}={msg_arg}.type,{sender_arg}==="background-copy")'
        content = re.sub(on_msg_pattern, replacement, content, count=1)
        print("    - onMessage listener patched to support bypass-tab-redirect state caching.")
    else:
        print("    - WARNING: Could not find onMessage listener to inject bypass redirection handler.")

    # 20. Make Lc() loop helper return false on Firefox (since offscreen viewer links are Chromium only)
    lc_helper_pattern = r'async\s+function\s+([a-zA-Z0-9_$]+)\(\)\s*\{\s*(for\s*\(\s*let\s+[a-zA-Z0-9_$]+\s+of\s+([a-zA-Z0-9_$]+)\s*\)\s*try\s*\{\s*return\s+await\s+fetch)'
    match_lc = re.search(lc_helper_pattern, content)
    if match_lc:
        func_name = match_lc.group(1)
        rem_code = match_lc.group(2)
        replacement = f'async function {func_name}(){{if(typeof browser!=="undefined")return!1;{rem_code}'
        content = re.sub(lc_helper_pattern, replacement, content, count=1)
        print("    - Lc Chromium-specific offscreen viewer fetch helper bypassed for Firefox.")
    else:
        print("    - WARNING: Could not find Lc offscreen viewer check to patch.")

    # 21. Append toolbar action onClicked listener
    installed_pattern = r'(chrome\.runtime\.onInstalled\.addListener\(.*?\}\);)'
    match_installed = re.search(installed_pattern, content, re.DOTALL)
    if match_installed:
        full_on_installed = match_installed.group(1)
        content = content.replace(
            full_on_installed,
            f'{full_on_installed}\nchrome.action.onClicked.addListener(a=>{{chrome.tabs.create({{url:chrome.runtime.getURL("reader.html")}})}});'
        )
        print("    - Extension toolbar action onClicked tab opener registered.")
    else:
        print("    - WARNING: Could not find onInstalled registration to append action click listener.")

    with open(bg_js_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] background-compiled.js patched successfully!")

def patch_reader_js(reader_js_path: Path):
    print(f"[*] Patching reader-compiled.js...")
    with open(reader_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove allow-same-origin from sandbox attribute of gsr-loader-iframe
    target = '.sandbox="allow-same-origin allow-scripts allow-downloads"'
    replacement = '.sandbox="allow-scripts allow-downloads"'
    if target in content:
        content = content.replace(target, replacement)
        print("    - Sandbox attribute modified: allow-same-origin removed.")
    else:
        # fallback regex if formatting differs
        content, count = re.subn(
            r'\.sandbox\s*=\s*["\']allow-same-origin\s+allow-scripts\s+allow-downloads["\']',
            replacement,
            content
        )
        print(f"    - Sandbox attribute modified (regex): {count} replacements.")

    # 2. Fix pop-up focus bubble events (TypeError when a.closest is not a function)
    # Replace: a.closest(".gsr-popover") with: ((a && typeof a.closest === "function") ? a.closest(".gsr-popover") : null)
    content, count2 = re.subn(
        r'([a-zA-Z0-9_$]+)\.closest\(\s*"\.gsr-popover"\s*\)',
        r'((\1&&typeof \1.closest==="function")?\1.closest(".gsr-popover"):null)',
        content
    )
    print(f"    - Popover closest selector guards: {count2}")

    with open(reader_js_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] reader-compiled.js patched successfully!")


def patch_pdf_loader_js(pdf_loader_path: Path):
    print(f"[*] Patching pdf_loader-compiled.js...")
    with open(pdf_loader_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Patch parent window postMessage targetOrigin checks
    # matches: window.parent.parent.postMessage({type:"fetch",url:a},a,[d.port2])
    # replaces target origin with computed value that handles unique origin / local file protocol
    post_msg_pattern = r'window\.parent\.parent\.postMessage\(\s*\{\s*type\s*:\s*"fetch"\s*,\s*url\s*:\s*([a-zA-Z0-9_$]+)\s*\}\s*,\s*\1\s*,\s*\[\s*([a-zA-Z0-9_$]+)\.port2\s*\]\s*\)'
    match = re.search(post_msg_pattern, content)
    if match:
        url_var = match.group(1)
        port_var = match.group(2)
        replacement = f'var targetOrigin=({url_var}.startsWith("file:")||window.parent.parent===window.parent)?(window.location.protocol+"//"+window.location.host):{url_var};window.parent.parent.postMessage({{type:"fetch",url:{url_var}}},targetOrigin,[{port_var}.port2])'
        content = re.sub(post_msg_pattern, replacement, content, count=1)
        print("    - Sandboxed iframe SOP postMessage target origin patched.")
    else:
        print("    - WARNING: Could not find postMessage target origin pattern to patch.")

    # 2. Fix pdf.js worker constructor fetching and blobifying security restrictions
    # replaces blob loader fetch block with direct relative url assignment
    worker_pattern = r'\(async\s*\(\)\s*=>\s*\{\s*var\s+([a-zA-Z0-9_$]+)\s*=\s*await\s+\(\s*await\s+fetch\(\s*"/pdf\.worker\.min\.js"\s*\)\s*\)\.blob\(\)\s*;\s*pdfjsLib\.GlobalWorkerOptions\.workerSrc\s*=\s*\(0\s*,\s*URL\.createObjectURL\)\s*\(\s*\1\s*\);'
    match_worker = re.search(worker_pattern, content)
    if match_worker:
        content = re.sub(worker_pattern, '(async()=>{pdfjsLib.GlobalWorkerOptions.workerSrc="/pdf.worker.min.js";', content, count=1)
        print("    - workerSrc blob loading bypassed with direct absolute URL mapping.")
    else:
        print("    - WARNING: Could not find workerSrc blob constructor to patch.")

    # 3. Patch PDF download handler to delegate download task to parent frame (since sandboxed null-origin frame cannot trigger downloads in Firefox)
    download_pattern = r'([a-zA-Z0-9_$]+)\s*=\s*async\s*function\s*\(\s*([a-zA-Z0-9_$]+)\s*,\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*if\s*\(\s*typeof\s+\3\s*===\s*"string"\s*&&\s*\(\s*\2\s*=\s*await\s*\(await\s*\(await\s*\2\.([a-zA-Z0-9_$]+)\)\.promise\)\.getData\(\)\s*,\s*window\.origin\s*===\s*"null"\s*\)\s*\)\s*\{\s*var\s+[a-zA-Z0-9_$]+\s*=\s*URL\.createObjectURL[\s\S]*?250\s*\)\s*\}\s*\}'
    match_download = re.search(download_pattern, content)
    if match_download:
        replacement = r'\1=async function(\2,\3){if(typeof \3==="string"&&(\2=await (await (await \2.\4).promise).getData())){window.parent.postMessage({type:"download_pdf",buffer:\2.buffer,filename:\3},"*")}}'
        content = re.sub(download_pattern, replacement, content, count=1)
        print("    - PDF download handler patched to use parent postMessage delegate.")
    else:
        print("    - WARNING: Could not find PDF download handler pattern to patch.")

    with open(pdf_loader_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] pdf_loader-compiled.js patched successfully!")

def patch_pdf_loader_iframe(pdf_iframe_path: Path):
    print(f"[*] Patching pdf_loader_iframe.html...")
    with open(pdf_iframe_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Add <meta charset="utf-8"> under <head> if not present
    if '<meta charset="utf-8">' not in html:
        html = html.replace("<head>", '<head>\n  <meta charset="utf-8">')

    with open(pdf_iframe_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("[+] pdf_loader_iframe.html patched successfully!")

def patch_universal_origin(file_path: Path):
    print(f"[*] Patching dynamic origin in {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Matches dynamic string additions: "chrome-extension://" + chrome.runtime.id or similar joins
    # or hardcoded Chrome IDs: "chrome-extension://dahenjhkoodjbpjheillcadbppiidmhp"
    content, count1 = re.subn(
        r'["\']chrome-extension://["\']\s*\+\s*chrome\.runtime\.id',
        'chrome.runtime.getURL("").slice(0,-1)',
        content
    )
    content, count2 = re.subn(
        r'["\']chrome-extension://[a-z]{32}["\']',
        'chrome.runtime.getURL("").slice(0,-1)',
        content
    )

    if count1 > 0 or count2 > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] {file_path.name} origin scheme patched: {count1 + count2} replacements.")
    else:
        print(f"[-] No origin scheme replacements found in {file_path.name}.")

def main():
    parser = argparse.ArgumentParser(description="Google Scholar PDF Reader Firefox Extension Patcher")
    parser.add_argument("input", help="Path to the source Google Scholar PDF Reader Chrome Extension zip file or directory")
    parser.add_argument("output", help="Path to save the patched Firefox extension output directory or zip file")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        print(f"[-] Error: Input path {input_path} does not exist.")
        sys.exit(1)

    # Determine temporary build folder
    build_dir = Path("./build_tmp").resolve()
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Extracting / copying source extension from {input_path}...")
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            zip_ref.extractall(build_dir)
    elif input_path.is_dir():
        shutil.copytree(input_path, build_dir, dirs_exist_ok=True)
    else:
        print("[-] Error: Input must be a zip file or a directory.")
        sys.exit(1)

    # Verify key source files are extracted
    required_files = [
        "manifest.json",
        "reader.html",
        "background-compiled.js",
        "reader-compiled.js",
        "pdf_loader-compiled.js",
        "contentscript-compiled.js",
        "historyscript-compiled.js",
        "reloadscript-compiled.js"
    ]
    for rf in required_files:
        if not (build_dir / rf).exists():
            print(f"[-] Error: Required extension file '{rf}' was not found in the source extension.")
            shutil.rmtree(build_dir)
            sys.exit(1)

    print("[+] Extension source extracted successfully.")

    # Deminify & format all extracted JS files first
    deminify_js_files(build_dir)

    # Apply patches
    patch_manifest(build_dir / "manifest.json")
    patch_locales(build_dir / "_locales" / "en" / "messages.json")
    patch_reader_html(build_dir / "reader.html")
    patch_background_js(build_dir / "background-compiled.js")
    patch_reader_js(build_dir / "reader-compiled.js")
    patch_pdf_loader_js(build_dir / "pdf_loader-compiled.js")
    patch_pdf_loader_iframe(build_dir / "pdf_loader_iframe.html")


    # Apply universal origin patches to scripts
    scripts_to_patch = [
        "contentscript-compiled.js",
        "historyscript-compiled.js",
        "reloadscript-compiled.js"
    ]
    for script in scripts_to_patch:
        patch_universal_origin(build_dir / script)

    # Copy our Firefox helper script to build folder
    helper_src = Path(__file__).parent / "reader_firefox_helper.js"
    if helper_src.exists():
        shutil.copy(helper_src, build_dir / "reader_firefox_helper.js")
        print("[+] Copied reader_firefox_helper.js to build directory.")
    else:
        print("[-] WARNING: reader_firefox_helper.js was not found in the patcher repo!")

    # Write patched files to destination
    print(f"[*] Packaging patched extension to {output_path}...")
    if output_path.suffix.lower() == ".zip":
        if output_path.exists():
            output_path.unlink()
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_out:
            for root, _, files in os.walk(build_dir):
                for file in files:
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(build_dir)
                    zip_out.write(file_path, rel_path)
        print(f"[+] Successfully generated patched zip at {output_path}")
    else:
        if output_path.exists():
            shutil.rmtree(output_path)
        shutil.copytree(build_dir, output_path)
        print(f"[+] Successfully saved patched extension folder to {output_path}")

    # Cleanup build_tmp
    shutil.rmtree(build_dir)
    print("[+] All patching completed successfully!")

if __name__ == "__main__":
    main()
