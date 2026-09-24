CLOSE_ON_UNLOAD_SCRIPT = """
    <script>
      (function () {
        if (window.top !== window) {
          return;
        }
        var allowShutdownOnClose = true;
        var markInternalNavigation = function () {
          allowShutdownOnClose = false;
        };
        document.addEventListener('click', function (event) {
          var anchor = event.target.closest && event.target.closest('a[href]');
          if (anchor && anchor.target !== '_blank' && !anchor.hasAttribute('download')) {
            markInternalNavigation();
          }
        }, true);
        document.addEventListener('submit', function (event) {
          if (!event.defaultPrevented) {
            markInternalNavigation();
          }
        });
        var nativeFormSubmit = HTMLFormElement.prototype.submit;
        HTMLFormElement.prototype.submit = function () {
          markInternalNavigation();
          return nativeFormSubmit.apply(this, arguments);
        };
        window.addEventListener('pagehide', function (event) {
          if (allowShutdownOnClose && !event.persisted) {
            navigator.sendBeacon('/shutdown');
          }
        });
      })();
    </script>
"""

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CORDHISK Web</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <style>
      :root {
        --bg: #eef3f6;
        --ink: #17212b;
        --brand: #e69f00;
        --brand-2: #56b4e9;
        --surface: #ffffff;
        --line: #b8c7d1;
        --shadow: 0 8px 24px rgba(91, 57, 30, 0.12);
      }
      body { font-family: "Avenir Next", "Segoe UI", sans-serif; margin: 0; background: var(--bg); color: var(--ink); }
      .shell { display: grid; grid-template-columns: 450px 1fr; height: 100vh; height: 100dvh; min-height: 0; align-items: stretch; overflow: hidden; }
      .sidebar { position: relative; background: #003b5c; color: white; padding: 20px; display: flex; flex-direction: column; height: 100vh; height: 100dvh; min-height: 0; box-sizing: border-box; overflow: hidden; }
      .app-heading { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
      .sidebar h2 { margin: 0; }
      .sidebar-subtitle { margin: 0 0 10px; font-size: 14px; }
      .content { height: 100vh; height: 100dvh; min-height: 0; padding: 24px; box-sizing: border-box; overflow: hidden; }
      .card { background: var(--surface); border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: var(--shadow); border: 1px solid rgba(219, 228, 240, 0.7); }
      a { color: #0f5b78; text-decoration: none; }
      .pill { display: inline-flex; align-items: center; margin: 3px; padding: 5px 10px; border-radius: 999px; background: #e2e8f0; font-size: 12px; border: 1px solid transparent; }
      .pill.memory { background: #fff1c7; color: #7a4f00; border-color: #e69f00; }
      .pill.cho { background: #d9f0e8; color: #075e54; border-color: #56b4e9; }
      .pill.add { background: #e69f00; color: #17212b; border-color: #b87900; cursor: pointer; font-weight: 700; min-width: 28px; justify-content: center; }
      .pill.remove { background: #e69f00; color: #2b2118; border-color: #b77900; cursor: pointer; font-weight: 700; min-width: 28px; justify-content: center; }
      .pill.selected { box-shadow: 0 0 0 2px #0f172a inset; }
      .text-view { font-family: inherit; font-size: 14px; line-height: 1.7; white-space: pre-line; }
      .text-view p { margin: 0 0 10px; }
      form input, form select, form textarea { width: 100%; margin-bottom: 10px; padding: 8px; box-sizing: border-box; }
      form textarea { min-height: 140px; }
      button { padding: 8px 12px; border: 0; border-radius: 8px; background: var(--brand); color: white; cursor: pointer; transition: transform 0.08s ease, opacity 0.12s ease; }
      button:hover { opacity: 0.96; }
      button:active { transform: translateY(1px); }
      .nav { margin-bottom: 14px; }
      .nav a { color: white; margin-right: 10px; }
      .highlight { padding: 0 2px; border-radius: 4px; color: #111827; }
      .highlight.memory { background: #f9d98c; }
      .highlight.cho { background: #a7d8d2; }
      .metadata-panel { margin: 14px 0 18px; }
      .metadata-panel summary { cursor: pointer; font-weight: 600; margin-bottom: 8px; }
      .metadata-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
      .metadata-section { border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
      .metadata-table { width: 100%; border-collapse: collapse; font-size: 13px; }
      .metadata-table th, .metadata-table td { text-align: left; padding: 6px 4px; border-bottom: 1px solid #eef2f7; }
      .metadata-table input { margin-bottom: 0; }
      .annotation-toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
      .annotation-toolbar button { padding: 6px 10px; }
      .graph-toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; margin: 12px 0 0; min-height: 28px; }
      .graph-toolbar button { box-sizing: border-box; height: 28px; padding: 5px 8px; border-radius: 4px; font-family: inherit; font-size: 11px; font-weight: 700; }
      .graph-hover-value { flex: 0 0 auto; min-width: 0; max-width: 100%; margin: 0; color: #17212b; font-size: 14px; font-weight: 400; line-height: 1.45; overflow-wrap: anywhere; }
      .graph-hover-value::before { content: none; }
      .grid { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 0.95fr); gap: 16px; height: calc(100vh - 48px); min-height: 0; align-items: stretch; }
      .graph-card { height: 100%; min-height: 0; display: flex; flex-direction: column; }
      .graph-shell { flex: 1 1 auto; min-height: 0; margin-top: 0; overflow: auto; border: 1px solid #b8c7d1; border-radius: 8px; background: #ffffff; }
      svg { display: block; width: 100%; min-width: 0; min-height: 100%; height: auto; border: 0; border-radius: 8px; background: #ffffff; cursor: grab; }
      svg.dragging { cursor: grabbing; }
      .node { stroke: #334155; stroke-width: 1.5; }
      .memory { fill: #d8ebf7; }
      .cho { fill: #e69f00; }
      .memory_metadata { fill: #d8ebf7; }
      .cho_metadata { fill: #d8f1e6; }
      .metadata-hidden { opacity: 0; visibility: hidden; pointer-events: none; }
      .metadata-visible { opacity: 1; visibility: visible; pointer-events: auto; }
      .metadata-collapsed { opacity: 0; visibility: hidden; pointer-events: none; }
      .edge-collapsed { opacity: 0; visibility: hidden; }
      .focused { stroke: black; stroke-width: 1; }
      .label { font-size: 12px; fill: #0f172a; pointer-events: none; }
      .result-table { width: 100%; border-collapse: collapse; font-size: 14px; }
      .result-table th, .result-table td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #e5e7eb; }
      .inline-form { display: flex; gap: 8px; align-items: end; flex-wrap: wrap; margin-top: 10px; }
      .inline-form > div { min-width: 160px; }
      .inline-form label { display: block; font-size: 12px; margin-bottom: 3px; }
      .notice { padding: 10px 12px; border-radius: 8px; margin-bottom: 14px; font-size: 14px; }
      .notice.success { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
      .notice.error { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
      .cta-btn { display: inline-block; padding: 9px 13px; border-radius: 6px; background: #0ea5e9; color: white; text-decoration: none; }
      .tag-section { margin: 14px 0 18px; }
      .tag-section h4 { margin: 0 0 8px; }
      .tag-help { color: #475569; font-size: 13px; margin: 0 0 8px; }
      .tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
      .tag-selector { display: inline-flex; align-items: center; cursor: pointer; }
      .tag-selector input { position: absolute; opacity: 0; pointer-events: none; }
      .tag-selector.empty { cursor: default; }
      .compact-tools { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
      .compact-tools .metadata-section h5 { margin-top: 0; }
      .cho-memory-group { margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #eef2f7; }
      .cho-memory-group:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: 0; }
      .meta-toggle { display: flex; gap: 8px; margin: 10px 0 12px; flex-wrap: wrap; }
      .meta-toggle a { display: inline-block; padding: 6px 10px; border-radius: 999px; font-size: 12px; border: 1px solid #bfdbfe; color: #1e3a8a; background: #eff6ff; }
      .meta-toggle a.active { color: white; background: #1d4ed8; border-color: #1d4ed8; }
      .metadata-card { position: sticky; top: 12px; }
      .metadata-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
      .metadata-inline-edit { display: none; margin-top: 10px; padding: 10px; border: 1px solid #dbeafe; border-radius: 8px; background: #f0f7ff; }
      .metadata-inline-edit-actions { margin-top: 8px; }
      .map-dialog { width: min(760px, calc(100vw - 32px)); border: 0; padding: 0; box-shadow: var(--shadow); }
      .map-dialog::backdrop { background: rgba(15, 23, 42, 0.55); }
      .map-dialog-body { padding: 16px; }
      .map-picker { height: 430px; margin: 12px 0; border: 1px solid var(--line); }
      .map-dialog-actions { display: flex; justify-content: flex-end; gap: 8px; }
      .coordinate-inputs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
      .coordinate-inputs label { display: block; font-size: 12px; margin-bottom: 3px; }
      .dialog-select { width: 100%; padding: 8px; box-sizing: border-box; }
      .annotation-inline-edit { display: none; margin-top: 10px; padding: 10px; border: 1px solid #bfdbfe; border-radius: 8px; background: #eff6ff; }
      #add-cho-tag-box.annotation-inline-edit { display: block; }
      .memory-mode-hide { display: none; }
      .sidebar-list { list-style: none; margin: 0; padding: 0; }
      .sidebar-list li { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
      .sidebar-list a { color: #2b2118; display: inline-block; max-width: 340px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
      .record-identity { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin: 0 0 10px; }
      .record-identity h4 { margin: 0; }
      .record-identity small { color: #6b5b4d; font-size: 11px; }
      .record-identity .record-label { color: #6b5b4d; font-size: 10px; font-weight: 700; }
      .mini-delete { width: 24px; min-width: 24px; height: 24px; line-height: 24px; padding: 0; border-radius: 999px; background: #facc15; color: #1f2937; font-weight: 700; font-size: 14px; }
      .sidebar-action { margin-bottom: 12px; }
      .sidebar-action button { width: 100%; background: #0ea5e9; }
      .sidebar-pop { display: none; margin-top: 8px; padding: 10px; border-radius: 8px; background: rgba(15, 23, 42, 0.45); border: 1px solid rgba(148, 163, 184, 0.4); }
      .sidebar-pop label { font-size: 12px; color: #bfdbfe; display: block; margin-bottom: 2px; }
      .sidebar-pop input, .sidebar-pop select { margin-bottom: 8px; }
      .sidebar-card { background: #fffaf2; }
      .sidebar-card h3 { color: #2b2118; }
      .sidebar-button-grid { display: flex; flex-direction: column; gap: 2px; min-width: 0; margin-bottom: 12px; padding: 4px 0; }
      .side-btn, .side-btn:visited { display: flex; align-items: center; justify-content: flex-start; width: 100%; min-width: 0; min-height: 30px; box-sizing: border-box; padding: 6px 10px; border-radius: 4px; color: #dbeafe; background: transparent; border: 0; font-size: 13px; font-weight: 600; text-align: left; }
      .side-btn:hover { background: rgba(255, 255, 255, 0.12); color: white; }
      .side-btn.close-app-btn { background: #7f1d1d; color: white; }
      .side-btn.close-app-btn:hover { background: #991b1b; color: white; }
      .side-btn.alt, .side-btn.alt:visited { color: #dbeafe; }
      .side-btn.alt:hover { background: rgba(255, 255, 255, 0.12); color: white; }
      .contextual-action { display: block; width: 100%; box-sizing: border-box; height: 28px; margin: 0; padding: 5px 8px; border: 1px solid #e69f00; border-radius: 4px; color: #003b5c; background: #ffffff; font-size: 11px; font-weight: 700; line-height: 16px; text-align: center; text-decoration: none; }
      .contextual-action:hover { background: #e6f2f8; color: #003b5c; }
      .contextual-action-row { display: flex; align-items: center; gap: 4px; flex: 0 0 auto; min-width: 0; min-height: 28px; flex-wrap: wrap; margin: 12px 0 20px; padding: 0 2px; clear: both; }
      .contextual-action-row .contextual-action { flex: 1 1 auto; width: auto; margin: 0; }
      .contextual-label { align-self: center; color: white; font-size: 10px; font-weight: 700; }
      .memory-controls-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0 0 12px; padding-bottom: 10px; border-bottom: 1px solid #d9c8b8; }
      .memory-controls-top .cho-filter-row { margin: 0; }
      .side-btn.disabled { pointer-events: none; opacity: 0.6; }
      .menu-toggle { display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px; margin: 0; padding: 0; border: 1px solid rgba(255, 255, 255, 0.35); border-radius: 5px; background: rgba(255, 255, 255, 0.1); font-size: 0; }
      .menu-toggle::before { content: "\\2630"; color: white; font-size: 22px; line-height: 1; }
      .menu-toggle.active { background: #009e73; }
      .sidebar-menu { position: absolute; top: 72px; left: 20px; right: 20px; z-index: 20; padding: 10px; border: 1px solid rgba(148, 163, 184, 0.45); border-radius: 8px; background: rgba(15, 59, 90, 0.98); box-shadow: 0 12px 28px rgba(15, 23, 42, 0.28); }
      .sidebar-menu.hidden { display: none; }
      .workspace-heading { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
      .workspace-heading h4 { margin: 0; }
      .workspace-identity { color: #475569; font-size: 13px; font-weight: 600; }
      .rdf-link { display: inline-flex; align-items: center; padding: 5px 8px; border-radius: 5px; background: #dbe8ed; color: #164e63; font-size: 12px; font-weight: 700; text-decoration: none; }
      .rdf-link:hover { background: #c5dce4; color: #0f3d4c; }
      .export-label { color: #6b5b4d; font-size: 10px; font-weight: 700; }
      .selection-value { font-style: italic; font-weight: 700; }
      .cho-tags-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
      .cho-tags-head h4 { margin: 0; }
      .cho-tags-head .toggle-cho-tags { background: #475569; padding: 6px 10px; font-size: 12px; }
      .cho-tags-head .toggle-cho-tags[aria-expanded="false"] { background: #64748b; }
      .cho-filter-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
      .cho-filter-row label { font-size: 12px; color: #475569; }
      .cho-filter-row select { width: auto; min-width: 120px; margin: 0; padding: 6px 8px; border: 0; border-radius: 5px; background: #f8fafc; color: #17212b; font-size: 12px; }
      .cho-filter-count { font-size: 12px; color: #64748b; white-space: nowrap; }
      .cho-tag-item.hidden { display: none; }
      .list-selector { display: grid; grid-template-columns: minmax(110px, 1.1fr) repeat(3, minmax(0, 1fr)); gap: 6px; margin-bottom: 8px; }
      .list-selector button { background: #334155; font-size: 12px; padding: 6px 8px; }
      .list-selector button.active { background: #e69f00; color: #17212b; }
      .list-selector .metadata-link { display: flex; align-items: center; justify-content: center; min-width: 0; box-sizing: border-box; padding: 6px 8px; border-radius: 5px; background: #334155; color: white; font-size: 12px; text-decoration: none; }
      .list-selector .metadata-link.active { background: #e69f00; color: #17212b; }
      .list-selector select { width: 100%; min-width: 0; margin: 0; padding: 6px 8px; border: 0; border-radius: 5px; background: #f8fafc; color: #17212b; font-size: 12px; }
      .metadata-management-tools { margin: 0 0 12px; padding: 12px; border: 1px solid rgba(255, 255, 255, 0.35); border-radius: 8px; background: rgba(0, 59, 92, 0.72); }
      .metadata-management-tools h3 { margin: 0 0 10px; font-size: 14px; }
      .metadata-management-tools .management-action { display: block; width: 100%; box-sizing: border-box; margin-bottom: 8px; padding: 7px 9px; border-radius: 4px; color: #dbeafe; background: rgba(255, 255, 255, 0.08); font-size: 12px; font-weight: 600; text-align: left; }
      .metadata-management-tools .management-action:hover { background: rgba(255, 255, 255, 0.16); color: white; }
      .metadata-management-tools form { margin: 0 0 10px; }
      .metadata-management-tools .metadata-import-form { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 6px; align-items: center; }
      .metadata-management-tools input[type="file"] { width: 100%; min-width: 0; margin: 0; color: #dbeafe; font-size: 11px; }
      .metadata-management-tools button { width: auto; max-width: 100%; box-sizing: border-box; padding: 7px 9px; border-radius: 4px; background: #dbe8ed; color: #164e63; font-size: 12px; font-weight: 700; }
      .metadata-management-tools .management-space-list { margin: 8px 0 0; padding: 0; list-style: none; }
      .metadata-management-tools .management-space-list li { display: flex; justify-content: space-between; gap: 8px; margin-top: 5px; font-size: 11px; }
      .metadata-management-tools .management-space-list a { color: #dbeafe; }
      .metadata-management-tools .management-space-list a:hover { color: white; }
      .workspace-frame { width: 100%; height: calc(100vh - 48px); min-height: 0; border: 0; border-radius: 8px; background: white; box-shadow: var(--shadow); }
      .sidebar-list-shell { flex: 1 1 0; min-height: 0; max-height: none; margin-bottom: 12px; overflow: hidden; }
      .sidebar-list-shell .list-panel { margin-bottom: 0; height: 100%; overflow-y: auto; }
      .list-panel.hidden { display: none; }
      .inline-annotation-row { display: grid; grid-template-columns: minmax(170px, 1fr) minmax(170px, 1fr) auto; gap: 8px; align-items: end; }
      .inline-annotation-row > div { min-width: 0; }
      .inline-annotation-row label { display: block; font-size: 12px; margin-bottom: 3px; }
      .inline-annotation-row input, .inline-annotation-row select { margin-bottom: 0; }
      .inline-annotation-row button { white-space: nowrap; }
      .status-msg { display: none; }
      .annotation-title { font-weight: 400; }
      .memory-title { margin: 0 0 10px; font-size: 1em; font-weight: 700; }
      .metadata-helper { color: #475569; font-size: 13px; margin: 0 0 8px; }
      .metadata-section-label { margin: 0 0 6px; color: #6b5b4d; font-size: 11px; font-weight: 700; }
      .cho-report-section { margin-top: 18px; }
      .cho-report-section h5 { margin: 0 0 6px; color: #7c2d12; font-size: 14px; }
      .cho-report-table { width: 100%; border-collapse: collapse; font-size: 14px; line-height: 1.45; }
      .cho-report-table th, .cho-report-table td { padding: 6px 4px; text-align: left; border-bottom: 1px solid #ead9c8; vertical-align: top; }
      .cho-report-table th:first-child { width: 42px; }
      .memory-tags-title { color: #1b1f24; }
      .right-panel { display: flex; flex-direction: column; height: 100%; min-height: 0; overflow: hidden; }
      .right-panel .metadata-card { order: 1; position: static; flex: 1 1 auto; min-height: 0; overflow-y: auto; }
      .right-panel .memory-text-card { order: 2; }
      .right-panel .project-footer-note { order: 3; flex: 0 0 auto; }
      .memory-text-card { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; }
      .memory-text-card form { display: flex; flex-direction: column; flex: 1; min-height: 0; }
      .memory-text-scroll { flex: 1; min-height: 0; max-height: none; overflow-y: auto; }
      .project-footer-note {
        margin-top: auto;
        padding-top: 12px;
        font-size: 11px;
        line-height: 1.35;
        color: #475569;
        border-top: 1px solid #d9c8b8;
      }
      @media (max-width: 980px) {
        .shell { grid-template-columns: 1fr; height: auto; min-height: 100vh; overflow: visible; }
        .sidebar { height: auto; min-height: auto; border-bottom: 1px solid #9a3412; }
        .grid { grid-template-columns: 1fr; height: auto; }
        .metadata-card { position: static; }
        .menu-toggle { display: block; }
        .sidebar-menu.hidden { display: none; }
        .sidebar-button-grid { grid-template-columns: 1fr; }
        .side-btn, .side-btn:visited, .sidebar-button-grid button { width: 100%; }
        .content { height: auto; min-height: 0; padding: 14px; overflow: visible; }
        .sidebar-list-shell { min-height: 180px; max-height: none; overflow: visible; }
        .card { padding: 12px; }
        .graph-card { height: auto; min-height: auto; }
        .right-panel { height: auto; min-height: 0; overflow: visible; }
        svg { min-width: 0; min-height: 0; }
        .inline-annotation-row { grid-template-columns: 1fr; }
        .memory-text-card { min-height: 420px; }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <aside class="sidebar">
        <div class="app-heading">
          <button type="button" class="menu-toggle" id="toggle-menu" aria-label="Open menu" title="Open menu">Menu</button>
          <h2>CORDHISK APP v3.0</h2>
        </div>
        <p class="sidebar-subtitle">Memories, metadata, and cultural heritage objects.</p>
        <div class="sidebar-menu hidden" id="sidebar-menu">
          <div class="sidebar-button-grid">
            <a class="side-btn" href="/?workspace=search">Search text in memories</a>
            <a class="side-btn" href="/?workspace=map">Open map for georeferenced memories</a>
            <a class="side-btn" href="/?workspace=compare">Quantitative report</a>
            <button type="button" id="close-app-btn" class="side-btn close-app-btn" title="Close the app safely">Close app</button>
          </div>
        </div>
        <div class="list-selector">
          <form method="get" action="/" style="display: contents;">
            {% if selected_memory and not focus_cho %}<input type="hidden" name="memory_id" value="{{ selected_memory.id }}">{% endif %}
            {% if focus_cho %}<input type="hidden" name="focus_cho" value="{{ focus_cho }}">{% endif %}
            {% if workspace %}<input type="hidden" name="workspace" value="{{ workspace }}">{% endif %}
            <select name="metadata_space" aria-label="Metadata Space" onchange="this.form.submit()">
              {% for space in metadata_spaces %}<option value="{{ space.name }}" {% if active_metadata_space and active_metadata_space.name == space.name %}selected{% endif %}>{{ space.name }}</option>{% endfor %}
            </select>
          </form>
          <button type="button" id="show-memories-btn" class="{% if not focus_cho and panel != 'chos' and not is_metadata_management %}active{% endif %}">Memories</button>
          <button type="button" id="show-chos-btn" class="{% if (focus_cho or panel == 'chos') and not is_metadata_management %}active{% endif %}">Objects</button>
          <a class="metadata-link{% if is_metadata_management %} active{% endif %}" id="show-metadata-btn" href="/?workspace=metadata_spaces&metadata_space={{ active_metadata_space.name }}">Metadata</a>
        </div>
        {% if is_metadata_management %}
        <div class="metadata-management-tools">
          <h3>Metadata Spaces</h3>
          <a class="management-action" href="/?workspace=metadata_space_create">Create Metadata Space</a>
          <a class="management-action" href="/?workspace=metadata_space_create&edit={{ active_metadata_space.name }}">See and edit current</a>
          <a class="management-action" href="/metadata-spaces/{{ active_metadata_space.name }}.csv">Download current</a>
          <form class="metadata-import-form" action="/metadata-spaces/import" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".csv,text/csv" required>
            <button type="submit">Import CSV</button>
          </form>
        </div>
        {% endif %}
        {% if not is_metadata_management %}
        <div class="sidebar-list-shell">
          <div class="card sidebar-card list-panel" id="memories-panel">
            <ul class="sidebar-list">
              {% for memory in memories %}
              <li>
                <a href="/?memory_id={{ memory.id }}">{{ memory.custom_id or memory.id }} — {{ memory.title or ('Memory ' ~ memory.id) }}</a>
                <form action="/memories/{{ memory.id }}/delete" method="post" onsubmit="return confirm('Delete this memory permanently?');">
                  <button type="submit" class="mini-delete" title="Delete memory">-</button>
                </form>
              </li>
              {% endfor %}
            </ul>
          </div>
          <div class="card sidebar-card list-panel hidden" id="chos-panel">
            <ul class="sidebar-list">
              {% for cho in chos %}
              <li>
                <a href="/?focus_cho={{ cho.custom_id or cho.id }}">{{ cho.custom_id or cho.id }} — {{ cho.title or cho.custom_id or cho.id }}</a>
                <form action="/chos/{{ cho.id }}/delete{% if selected_memory %}?memory_id={{ selected_memory.id }}{% endif %}" method="post" onsubmit="return confirm('Delete this object and remove its tags from all memories?');">
                  <button type="submit" class="mini-delete" title="Delete object">-</button>
                </form>
              </li>
              {% endfor %}
            </ul>
          </div>
          <div class="card sidebar-card list-panel hidden" id="tags-panel">
            {% if selected_memory %}
            <div id="memory-tags-panel">
              <div class="cho-tags-head memory-tags-title">
              </div>
              <form action="/memories/{{ selected_memory.id }}/edit" method="post" id="memory-metadata-form">
                <input type="hidden" name="focus_cho" value="{{ focus_cho or '' }}">
                <input type="hidden" id="inline-edit-field" name="edit_memory_metadata_field" value="">
                <input type="hidden" id="inline-edit-value" name="edit_memory_metadata_value" value="">

                <div class="memory-controls-top">
                  <button type="button" class="pill add" id="open-add-memory-tag" title="Add memory metadata">Add</button>
                  <button type="button" class="pill remove" id="open-edit-memory-id" title="Edit memory identifier">Edit ID</button>
                  <button type="submit" class="pill remove" name="remove_selected" value="1" title="Remove selected metadata" onclick="return confirm('Remove selected metadata tags?');">Remove</button>
                  <div class="cho-filter-row">
                    <select id="cho-tag-filter" name="cho_tag_filter">
                      <option value="">All objects</option>
                    </select>
                    <span id="cho-tag-count" class="cho-filter-count"></span>
                  </div>
                </div>

                <div class="tag-section">
                  <div class="metadata-section-label">Memory Metadata</div>
                  <div class="tag-list">
                    {% if selected_memory.license %}
                    <label class="tag-selector">
                      <input type="checkbox" name="delete_memory_metadata[dc:license]" value="1">
                      <span class="pill memory memory-editable" data-memory-field="dc:license" data-memory-value="{{ selected_memory.license }}">dc:license: {{ selected_memory.license }}</span>
                    </label>
                    {% endif %}
                    {% for md in memory_metadata_items %}
                    <label class="tag-selector">
                      <input type="checkbox" name="delete_memory_metadata[{{ md.field }}]" value="1">
                      <span class="pill memory memory-editable" data-memory-field="{{ md.field }}" data-memory-value="{{ md.value }}">{{ md.label }}: {{ md.value }}</span>
                    </label>
                    {% else %}
                    <span class="pill memory">No memory metadata</span>
                    {% endfor %}
                  </div>
                </div>

                <div id="add-memory-tag-box" class="metadata-inline-edit">
                  <label>Field</label>
                  <select name="new_memory_metadata_field" id="new-memory-metadata-field">
                    <option value="">Choose metadata field</option>
                    <option value="__license__">License</option>
                    <option value="__coordinates__">Coordinates</option>
                    {% for field in memory_fields %}
                    <option value="{{ field.field }}">{{ field.label }}</option>
                    {% endfor %}
                  </select>
                  <label>Value</label>
                  <input name="new_memory_metadata_value" id="new-memory-metadata-value" placeholder="New value">
                  <div class="metadata-inline-edit-actions">
                    <button type="submit">Save metadata changes</button>
                  </div>
                </div>
                <input id="memory-latitude" name="memory_latitude" type="hidden" value="{{ memory_coordinates['wgs84_pos:lat'] }}">
                <input id="memory-longitude" name="memory_longitude" type="hidden" value="{{ memory_coordinates['wgs84_pos:long'] }}">

                <div class="tag-section">
                  <div class="metadata-section-label">Object metadata</div>
                  <div class="tag-list cho-tags-list" id="cho-tags-list">
                    {% for md in cho_metadata_items %}
                    <label class="tag-selector cho-tag-item" data-cho-id="{{ md.cho }}" data-cho-label="{{ md.label }}">
                      <input type="checkbox" name="delete_cho_metadata[{{ md.index }}]" value="1">
                      <span class="pill cho cho-tag-link" data-cho-tag-index="{{ md.index }}" data-metadata-field="{{ md.field }}" data-metadata-value="{{ md.value }}">{{ md.label }} / {{ md.label_field }}: {{ md.value }}</span>
                    </label>
                    {% else %}
                    <span class="pill cho">No object metadata</span>
                    {% endfor %}
                  </div>
                </div>
              </form>
            </div>
            {% else %}
            <p>Select a memory to edit memory and object tags.</p>
            {% endif %}
          </div>
        </div>
        {% if not focus_cho and panel != 'chos' %}
        <div class="contextual-action-row">
          <span class="contextual-label">Import</span>
          <a class="contextual-action" href="/?workspace=import">.txt</a>
          <span class="contextual-label">Export</span>
          {% if selected_memory %}
          <a class="contextual-action" href="/export/memory/{{ selected_memory.id }}.rdf">.rdf</a>
          <a class="contextual-action" href="/export/memory/{{ selected_memory.id }}.csv?metadata_space={{ active_metadata_space.name }}">.csv</a>
          <a class="contextual-action" href="/export/memory/{{ selected_memory.id }}.txt">.txt</a>
          {% else %}
          <a class="contextual-action" href="#" onclick="alert('Select a memory first.'); return false;">.rdf</a>
          <a class="contextual-action" href="#" onclick="alert('Select a memory first.'); return false;">.csv</a>
          <a class="contextual-action" href="#" onclick="alert('Select a memory first.'); return false;">.txt</a>
          {% endif %}
        </div>
        {% endif %}
        {% if panel == 'chos' or focus_cho %}
        <div class="contextual-action-row">
          <button type="button" class="contextual-action" id="open-add-cho">Add Object</button>
          <span class="contextual-label">Export</span>
          {% if selected_cho_details %}
          <a class="contextual-action" href="/export/cho?cho_id={{ selected_cho_details.label }}&mode=all">.rdf</a>
          <a class="contextual-action" href="/compare/report.csv?cho_id={{ selected_cho_details.label }}&metadata_space={{ active_metadata_space.name }}">.csv</a>
          {% else %}
          <a class="contextual-action" href="#" onclick="alert('Select an object first.'); return false;">.rdf</a>
          <a class="contextual-action" href="#" onclick="alert('Select an object first.'); return false;">.csv</a>
          {% endif %}
        </div>
        <form id="add-cho-pop" class="sidebar-pop" action="/chos/create" method="post">
          <label>Object ID</label>
          <input name="custom_id" placeholder="e.g. PR99" required>
          <label>Title</label>
          <input name="title" placeholder="Object name">
          <button type="submit">Create Object</button>
        </form>
        {% endif %}
        {% endif %}
      </aside>
      <main class="content">
        {% if notice_message %}
        <div class="status-msg" aria-hidden="true">{{ notice_message }}</div>
        {% endif %}
        {% if workspace_url %}
        <iframe class="workspace-frame" src="{{ workspace_url }}" title="{{ workspace_title }}"></iframe>
        {% elif selected_memory or focus_cho or graph_page %}
        <div class="grid">
          <div class="card graph-card">
            <div id="graph-hover-value" class="graph-hover-value">Hover object or metadata nodes to inspect values.</div>
            <div class="graph-shell">
                <svg id="graph-svg" viewBox="0 0 1000 {{ graph_height }}" role="img" aria-label="Memory and object graph">
                <g id="graph-content">
                  {% for edge in edges %}
                  <line x1="{{ edge[0].x }}" y1="{{ edge[0].y }}" x2="{{ edge[1].x }}" y2="{{ edge[1].y }}" data-from-id="{{ edge[0].id }}" data-to-id="{{ edge[1].id }}" stroke="#94a3b8" stroke-width="2"></line>
                  {% endfor %}
                  {% for node in nodes %}
                  <a href="{{ node.link }}">
                    <circle class="graph-node node {{ node.group }} {% if node.id == ('cho:' ~ focus_cho) or node.id == focus_memory %}focused{% endif %} {% if node.group in ['memory_metadata','cho_metadata'] %}metadata-visible{% endif %}" data-node-id="{{ node.id }}" data-node-type="{{ node.group }}" data-parent-id="{{ node.parent_id or '' }}" data-memory-owner-id="{{ node.memory_owner_id or '' }}" data-metadata-field="{{ node.metadata_field or '' }}" data-metadata-value="{{ node.metadata_value or '' }}" data-details="{{ node.details or '' }}" title="{{ node.details or '' }}" cx="{{ node.x }}" cy="{{ node.y }}" r="{{ node.radius or 32 }}"></circle>
                    <text class="label {% if node.group in ['memory_metadata','cho_metadata'] %}graph-metadata-label metadata-visible{% endif %}" data-node-id="{{ node.id }}" data-node-type="{{ node.group }}" data-parent-id="{{ node.parent_id or '' }}" data-memory-owner-id="{{ node.memory_owner_id or '' }}" x="{{ node.x }}" y="{{ node.y + 6 }}" text-anchor="middle">{% if node.group in ['memory', 'cho'] and node.label_top %}<tspan x="{{ node.x }}" dy="-7">{{ node.label_top }}</tspan><tspan x="{{ node.x }}" dy="14">{{ node.label_bottom }}</tspan>{% else %}{{ node.label }}{% endif %}</text>
                  </a>
                  {% endfor %}
                </g>
              </svg>
            </div>
            <div class="graph-toolbar">
              <button type="button" id="zoom-in" aria-label="Zoom in">+</button>
              <button type="button" id="zoom-out" aria-label="Zoom out">-</button>
              <button type="button" id="reset-view">Reset</button>
              <button type="button" id="download-graph">Download SVG</button>
              <button type="button" id="download-graph-png">Download PNG</button>
            </div>
          </div>
          <div class="right-panel">
            {% if not focus_cho %}
            <div class="card memory-text-card">
              <div class="workspace-heading">
                <div class="record-identity">
                  <h4 class="memory-title"><span class="record-label">ID:</span> {{ selected_memory.custom_id or selected_memory.id }} <span class="record-label">Name:</span> {{ selected_memory.title or ('Memory ' ~ selected_memory.id) }}</h4>
                </div>
              </div>
              <form action="/memories/{{ selected_memory.id }}/annotate" method="post" id="memory-annotation-form">
                <p class="annotation-title metadata-helper">Annotate highlighted memory text</p>
                <div class="annotation-toolbar">
                  <span id="selection-preview">No selection yet</span>
                </div>
                <div id="add-cho-tag-box" class="annotation-inline-edit">
                <div class="inline-annotation-row">
                  <div>
                    <label>Object</label>
                    <select name="annotation_cho">
                      {% for cho in chos %}
                      <option value="{{ cho.custom_id or cho.id }}"{% if selected_annotation_cho == (cho.custom_id or cho.id|string) %} selected{% endif %}>{{ cho.custom_id or cho.id }}{% if cho.title %} ({{ cho.title }}){% endif %}</option>
                      {% endfor %}
                    </select>
                  </div>
                  <div>
                    <label>Field</label>
                    <select name="annotation_field">
                      {% for field in cho_fields %}
                      <option value="{{ field.field }}">{{ field.label }}</option>
                      {% endfor %}
                    </select>
                  </div>
                  <div>
                    <button type="submit">Add</button>
                  </div>
                </div>
                </div>
                <div id="annotation-source" class="text-view memory-text-scroll" style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; margin-bottom: 10px; user-select: text;">
                  {% for paragraph in paragraphs %}
                  <p>{% for part in paragraph %}{% if part.type == 'text' %}{{ part.value }}{% else %}<span class="highlight {{ part.kind }}" title="{{ part.display_field }}"{% if part.cho_tag_index is not none %} data-cho-tag-index="{{ part.cho_tag_index }}"{% endif %}>{{ part.value }}</span>{% endif %}{% endfor %}</p>
                  {% endfor %}
                </div>
                <input id="selected-annotation-text" name="selected_annotation_text" type="hidden">
                <input id="selected-annotation-occurrence" name="selected_annotation_occurrence" type="hidden" value="0">
                <input type="hidden" name="focus_cho" value="{{ focus_cho or '' }}">
              </form>
            </div>
            {% endif %}
            {% if focus_cho %}
            <div class="card metadata-card">
              {% if selected_cho_details %}
                <div class="workspace-heading">
                  <div class="record-identity">
                    <h4><span class="record-label">ID:</span> {{ selected_cho_details.label }} <span class="record-label">Name:</span> {{ selected_cho_details.title }}</h4>
                  </div>
                </div>
                {% for section in cho_report_sections %}
                <section class="cho-report-section">
                  <h5>{{ section.display_field }}</h5>
                  <table class="cho-report-table">
                    <thead><tr><th>N</th><th>Instance</th><th>Related memories</th></tr></thead>
                    <tbody>
                    {% for row in section.rows %}
                    <tr><td>{{ row.count }}</td><td>{{ row.value }}</td><td>{% for memory in row.memories %}<a href="/?memory_id={{ memory.id }}&filter_cho={{ selected_cho_details.label }}">{{ memory.label }}</a>{% if not loop.last %}, {% endif %}{% endfor %}</td></tr>
                    {% endfor %}
                    </tbody>
                  </table>
                </section>
                {% endfor %}
                {% if not cho_report_sections %}
                <p>No metadata found for this CHO in the current memories.</p>
                {% endif %}
              {% elif focus_cho %}
                <p>Select an object from the sidebar or graph to view object metadata grouped by memory.</p>
              {% endif %}
            </div>
            {% endif %}
            <p class="project-footer-note">
              Developped by Rafael Ramirez Eudave at the Delft University of Technology (2026).<br>
              The "Community-driven Digitisation for Heritage at Risk" (CORDHISK) project is funded by the European Union's Horizon Europe 2023 (Marie Sklodowska Curie grant agreement No 101149833).
            </p>
          </div>
        </div>
        {% else %}
        {% if panel not in ['memories', 'chos'] %}
        <div class="card">
          {% if not panel and not workspace_url %}
          <h2>Welcome to CORDHISK App v3.0</h2>
          <p>Select a memory or CHO from the left panel to begin.</p>
          <p>Use the Metadata switch to choose the scheme used to interpret, create, and compare annotations.</p>
          <p>Use Report from the menu to inspect metadata across memories.</p>
          {% endif %}
        </div>
        {% endif %}
        {% endif %}
      </main>
    </div>
    <dialog class="map-dialog" id="memory-id-dialog">
      <div class="map-dialog-body">
        <h3>Edit memory identifier</h3>
        <input id="memory-custom-id" name="custom_id" value="{{ selected_memory.custom_id or selected_memory.id if selected_memory else '' }}" required form="memory-metadata-form">
        <div class="map-dialog-actions">
          <button type="button" id="cancel-memory-id">Cancel</button>
          <button type="submit" name="save_memory_identifier" value="1" form="memory-metadata-form">Save changes</button>
        </div>
      </div>
    </dialog>
    <dialog class="map-dialog" id="license-dialog">
      <div class="map-dialog-body">
        <h3>Choose a license</h3>
        <select class="dialog-select" id="memory-license-value" name="memory_license" form="memory-metadata-form">
          <option value="">Select a license</option>
          {% for license_option in memory_license_options %}
          <option value="{{ license_option }}" {% if selected_memory and selected_memory.license == license_option %}selected{% endif %}>{{ license_option }}</option>
          {% endfor %}
        </select>
        <div class="map-dialog-actions">
          <button type="button" id="cancel-license">Cancel</button>
          <button type="submit" name="save_memory_license" value="1" form="memory-metadata-form">Save changes</button>
        </div>
      </div>
    </dialog>
    <dialog class="map-dialog" id="map-dialog">
      <div class="map-dialog-body">
        <h3>Choose memory coordinates</h3>
        <div class="coordinate-inputs">
          <div>
            <label for="map-latitude">Latitude</label>
            <input id="map-latitude" type="number" step="any" min="-90" max="90" placeholder="e.g. 52.0116">
          </div>
          <div>
            <label for="map-longitude">Longitude</label>
            <input id="map-longitude" type="number" step="any" min="-180" max="180" placeholder="e.g. 4.3571">
          </div>
        </div>
        <div id="coordinate-map" class="map-picker"></div>
        <div class="map-dialog-actions">
          <button type="button" id="cancel-map-picker">Cancel</button>
          <button type="button" id="add-map-coordinates">Add coordinates</button>
        </div>
      </div>
    </dialog>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
      document.addEventListener('DOMContentLoaded', function () {
        const isChoView = {{ 'true' if focus_cho else 'false' }};
        const source = document.getElementById('annotation-source');
        const target = document.getElementById('selected-annotation-text');
        const targetOccurrence = document.getElementById('selected-annotation-occurrence');
        const preview = document.getElementById('selection-preview');
        const memoryAnnotationForm = document.getElementById('memory-annotation-form');
        const addChoTagBox = document.getElementById('add-cho-tag-box');
        const menuToggleButton = document.getElementById('toggle-menu');
        const sidebarMenu = document.getElementById('sidebar-menu');
        const closeAppButton = document.getElementById('close-app-btn');
        const svg = document.getElementById('graph-svg');
        const graphContent = document.getElementById('graph-content');
        const hoverValueBox = document.getElementById('graph-hover-value');
        const zoomInButton = document.getElementById('zoom-in');
        const zoomOutButton = document.getElementById('zoom-out');
        const resetButton = document.getElementById('reset-view');
        const downloadGraphButton = document.getElementById('download-graph');
        const downloadGraphPngButton = document.getElementById('download-graph-png');
        const graphDownloadName = {{ graph_download_name | tojson }};
        const safeGraphDownloadName = graphDownloadName.trim().replace(/[^a-zA-Z0-9._-]+/g, '_').replace(/^[.]+|[.]+$/g, '') || 'cordhisk-graph';
        const addMemoryTagButton = document.getElementById('open-add-memory-tag');
        const addMemoryTagBox = document.getElementById('add-memory-tag-box');
        const newMemoryMetadataField = document.getElementById('new-memory-metadata-field');
        const newMemoryMetadataValue = document.getElementById('new-memory-metadata-value');
        const memoryMetadataForm = document.getElementById('memory-metadata-form');
        const inlineEditField = document.getElementById('inline-edit-field');
        const inlineEditValue = document.getElementById('inline-edit-value');
        const openAddCho = document.getElementById('open-add-cho');
        const addChoPop = document.getElementById('add-cho-pop');
        const openEditMemoryId = document.getElementById('open-edit-memory-id');
        const memoryIdDialog = document.getElementById('memory-id-dialog');
        const cancelMemoryId = document.getElementById('cancel-memory-id');
        const showMemoriesBtn = document.getElementById('show-memories-btn');
        const showChosBtn = document.getElementById('show-chos-btn');
        const showMetadataBtn = document.getElementById('show-metadata-btn');
        const memoriesPanel = document.getElementById('memories-panel');
        const chosPanel = document.getElementById('chos-panel');
        const tagsPanel = document.getElementById('tags-panel');
        const choTagFilter = document.getElementById('cho-tag-filter');
        const choTagCount = document.getElementById('cho-tag-count');
        const choTagItems = Array.from(document.querySelectorAll('.cho-tag-item'));
        const choTagsList = document.getElementById('cho-tags-list');
        const latitudeInput = document.getElementById('memory-latitude');
        const longitudeInput = document.getElementById('memory-longitude');
        const licenseDialog = document.getElementById('license-dialog');
        const cancelLicense = document.getElementById('cancel-license');
        const mapDialog = document.getElementById('map-dialog');
        const mapLatitudeInput = document.getElementById('map-latitude');
        const mapLongitudeInput = document.getElementById('map-longitude');
        const cancelMapPicker = document.getElementById('cancel-map-picker');
        const addMapCoordinates = document.getElementById('add-map-coordinates');
        const initialChoTagFilter = {{ filter_cho | tojson }};
        const scrollStateKey = 'cordhisk:scroll:{{ selected_memory.id if selected_memory else "none" }}';
        let zoomLevel = 1;
        let panX = 0;
        let panY = 0;
        let isDragging = false;
        let startX = 0;
        let startY = 0;
        let coordinateMap;
        let coordinateMarker;
        let selectedCoordinates;
        let selectList;

        function captureSelection() {
          const selection = window.getSelection();
          const selectedText = selection ? selection.toString() : '';
          const trimmedSelection = selectedText.trim();
          if (!trimmedSelection) {
            preview.textContent = 'No selection yet';
            if (target) {
              target.value = '';
            }
            if (targetOccurrence) {
              targetOccurrence.value = '0';
            }
            return;
          }
          let occurrence = 0;
          if (selection && selection.rangeCount > 0 && source) {
            const range = selection.getRangeAt(0);
            if (source.contains(range.startContainer) && source.contains(range.endContainer)) {
              const leadingTrimmedChars = selectedText.length - selectedText.trimStart().length;
              const preRange = range.cloneRange();
              preRange.selectNodeContents(source);
              preRange.setEnd(range.startContainer, range.startOffset);
              const startOffset = preRange.toString().length + leadingTrimmedChars;
              const sourceText = source.textContent || '';
              let searchFrom = 0;
              while (true) {
                const hit = sourceText.indexOf(trimmedSelection, searchFrom);
                if (hit === -1 || hit >= startOffset) {
                  break;
                }
                occurrence += 1;
                searchFrom = hit + Math.max(trimmedSelection.length, 1);
              }
            }
          }
          if (target) {
            target.value = trimmedSelection;
          }
          if (targetOccurrence) {
            targetOccurrence.value = String(occurrence);
          }
          preview.innerHTML = 'Selection: <span class="selection-value"></span>';
          const valueSpan = preview.querySelector('.selection-value');
          if (valueSpan) {
            valueSpan.textContent = trimmedSelection;
          }
        }

        function saveTextScrollState() {
          if (!source) {
            return;
          }
          try {
            const payload = {
              sourceScrollTop: source.scrollTop,
              pageScrollY: window.scrollY || window.pageYOffset || 0,
            };
            window.sessionStorage.setItem(scrollStateKey, JSON.stringify(payload));
          } catch (error) {
            return;
          }
        }

        function restoreTextScrollState() {
          if (!source) {
            return;
          }
          try {
            const rawState = window.sessionStorage.getItem(scrollStateKey);
            if (!rawState) {
              return;
            }
            const state = JSON.parse(rawState);
            if (typeof state.sourceScrollTop === 'number') {
              source.scrollTop = state.sourceScrollTop;
            }
            if (typeof state.pageScrollY === 'number') {
              window.scrollTo(0, state.pageScrollY);
            }
          } catch (error) {
            return;
          }
        }

        requestAnimationFrame(function () {
          restoreTextScrollState();
          requestAnimationFrame(restoreTextScrollState);
        });

        if (source && target && preview) {
          source.addEventListener('mouseup', function () { setTimeout(captureSelection, 0); });
          source.addEventListener('scroll', saveTextScrollState, { passive: true });
        }

        if (downloadGraphButton && svg) {
          const serializeGraph = function () {
            const graphCopy = svg.cloneNode(true);
            graphCopy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            graphCopy.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
            const bounds = graphContent.getBBox();
            const padding = 40;
            const exportX = bounds.x - padding;
            const exportY = bounds.y - padding;
            const exportWidth = Math.max(1, bounds.width + padding * 2);
            const exportHeight = Math.max(1, bounds.height + padding * 2);
            graphCopy.setAttribute('viewBox', `${exportX} ${exportY} ${exportWidth} ${exportHeight}`);
            graphCopy.setAttribute('width', String(Math.ceil(exportWidth)));
            graphCopy.setAttribute('height', String(Math.ceil(exportHeight)));
            const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
            style.textContent = '.node { stroke: #334155; stroke-width: 1.5; } .memory { fill: #d8ebf7; } .cho { fill: #e69f00; } .memory_metadata { fill: #d8ebf7; } .cho_metadata { fill: #d8f1e6; } .label { font-family: sans-serif; font-size: 12px; fill: #0f172a; } .focused { stroke: black; stroke-width: 2; } line { stroke: #94a3b8; stroke-width: 2; }';
            graphCopy.insertBefore(style, graphCopy.firstChild);
            return {
              serialized: new XMLSerializer().serializeToString(graphCopy),
              width: Math.ceil(exportWidth),
              height: Math.ceil(exportHeight),
            };
          };

          downloadGraphButton.addEventListener('click', function () {
            const graph = serializeGraph();
            const blob = new Blob([graph.serialized], { type: 'image/svg+xml;charset=utf-8' });
            const downloadUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = safeGraphDownloadName + '.svg';
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(downloadUrl);
          });

          if (downloadGraphPngButton) {
            downloadGraphPngButton.addEventListener('click', function () {
              const graph = serializeGraph();
              const svgBlob = new Blob([graph.serialized], { type: 'image/svg+xml;charset=utf-8' });
              const svgUrl = URL.createObjectURL(svgBlob);
              const image = new Image();
              image.onload = function () {
                const scale = 2;
                const canvas = document.createElement('canvas');
                canvas.width = graph.width * scale;
                canvas.height = graph.height * scale;
                const context = canvas.getContext('2d');
                context.fillStyle = '#ffffff';
                context.fillRect(0, 0, canvas.width, canvas.height);
                context.drawImage(image, 0, 0, canvas.width, canvas.height);
                URL.revokeObjectURL(svgUrl);
                const link = document.createElement('a');
                link.href = canvas.toDataURL('image/png');
                link.download = safeGraphDownloadName + '.png';
                document.body.appendChild(link);
                link.click();
                link.remove();
              };
              image.src = svgUrl;
            });
          }
        }

        document.querySelectorAll('.cho-tag-link[data-cho-tag-index]').forEach(function (tag) {
          tag.addEventListener('click', function (event) {
            event.preventDefault();
            const checkbox = tag.closest('.tag-selector').querySelector('input[type="checkbox"]');
            checkbox.checked = !checkbox.checked;
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            const tagIndex = tag.getAttribute('data-cho-tag-index');
            const targetSpan = source && source.querySelector('.highlight.cho[data-cho-tag-index="' + tagIndex + '"]');
            if (targetSpan) {
              const sourceBounds = source.getBoundingClientRect();
              const targetBounds = targetSpan.getBoundingClientRect();
              source.scrollTo({
                top: source.scrollTop + targetBounds.top - sourceBounds.top - (source.clientHeight - targetBounds.height) / 2,
                behavior: 'smooth',
              });
            }
          });
        });

        window.addEventListener('beforeunload', saveTextScrollState);

        if (memoryAnnotationForm) {
          memoryAnnotationForm.addEventListener('submit', saveTextScrollState);
        }

        if (addChoTagBox) {
          addChoTagBox.style.display = 'block';
        }

        if (menuToggleButton && sidebarMenu) {
          const closeMenu = function () {
            menuToggleButton.classList.remove('active');
            sidebarMenu.classList.add('hidden');
          };
          const syncMenu = function () {
            if (!menuToggleButton.classList.contains('active')) {
              closeMenu();
            }
          };
          menuToggleButton.addEventListener('click', function () {
            const open = menuToggleButton.classList.toggle('active');
            sidebarMenu.classList.toggle('hidden', !open);
          });
          document.addEventListener('click', function (event) {
            if (!sidebarMenu.classList.contains('hidden')
              && !sidebarMenu.contains(event.target)
              && !menuToggleButton.contains(event.target)) {
              closeMenu();
            }
          });
          window.addEventListener('resize', syncMenu);
          syncMenu();
        }

        if (closeAppButton) {
          closeAppButton.addEventListener('click', function () {
            const confirmed = window.confirm('Are you sure you want to close CORDHISK?');
            if (!confirmed) {
              return;
            }

            fetch('/shutdown', {
              method: 'POST',
              credentials: 'same-origin',
            }).finally(function () {
              if (typeof window.close === 'function') {
                try {
                  window.close();
                } catch (error) {
                  // Browsers may block automatic closing; fallback to a blank page.
                }
              }
              window.location.href = 'about:blank';
            });
          });
        }

        document.querySelectorAll('.tag-selector input').forEach(function (input) {
          const label = input.closest('.tag-selector');
          const pill = label ? label.querySelector('.pill') : null;
          const syncSelectedState = function () {
            if (pill) {
              pill.classList.toggle('selected', input.checked);
            }
          };
          input.addEventListener('change', syncSelectedState);
          input.addEventListener('change', function () {
            if (!input.checked) {
              return;
            }
            document.querySelectorAll('.tag-selector input').forEach(function (otherInput) {
              if (otherInput === input) {
                return;
              }
              otherInput.checked = false;
              const otherLabel = otherInput.closest('.tag-selector');
              const otherPill = otherLabel ? otherLabel.querySelector('.pill') : null;
              if (otherPill) {
                otherPill.classList.remove('selected');
              }
            });
          });
          syncSelectedState();
        });

        document.querySelectorAll('.memory-editable').forEach(function (pill) {
          pill.addEventListener('dblclick', function () {
            if (!memoryMetadataForm || !inlineEditField || !inlineEditValue) {
              return;
            }
            const field = pill.getAttribute('data-memory-field') || '';
            const currentValue = pill.getAttribute('data-memory-value') || '';
            if (!field) {
              return;
            }
            if (field === 'dc:license') {
              const licenseValue = document.getElementById('memory-license-value');
              if (licenseDialog && licenseValue) {
                licenseValue.value = currentValue;
                licenseDialog.showModal();
              }
              return;
            }
            const updated = window.prompt('Update value for ' + field, currentValue);
            if (updated === null) {
              return;
            }
            const trimmed = updated.trim();
            if (!trimmed) {
              return;
            }
            inlineEditField.value = field;
            inlineEditValue.value = trimmed;
            memoryMetadataForm.submit();
          });
        });

        if (addMemoryTagButton && addMemoryTagBox) {
          addMemoryTagButton.addEventListener('click', function () {
            const isVisible = addMemoryTagBox.style.display === 'block';
            addMemoryTagBox.style.display = isVisible ? 'none' : 'block';
          });
        }

        if (newMemoryMetadataField) {
          newMemoryMetadataField.addEventListener('change', function () {
            const selectedField = newMemoryMetadataField.value;
            if (selectedField === '__license__' && licenseDialog) {
              newMemoryMetadataField.value = '';
              licenseDialog.showModal();
            } else if (selectedField === '__coordinates__') {
              newMemoryMetadataField.value = '';
              openCoordinatePicker();
            } else if (newMemoryMetadataValue) {
              newMemoryMetadataValue.focus();
            }
          });
        }

        if (cancelLicense && licenseDialog) {
          cancelLicense.addEventListener('click', function () {
            licenseDialog.close();
          });
        }

        if (openAddCho && addChoPop) {
          openAddCho.addEventListener('click', function () {
            const open = addChoPop.style.display === 'block';
            addChoPop.style.display = open ? 'none' : 'block';
          });
        }

        if (openEditMemoryId && memoryIdDialog) {
          openEditMemoryId.addEventListener('click', function () {
            memoryIdDialog.showModal();
            const memoryIdInput = document.getElementById('memory-custom-id');
            if (memoryIdInput) {
              memoryIdInput.focus();
              memoryIdInput.select();
            }
          });
        }

        if (cancelMemoryId && memoryIdDialog) {
          cancelMemoryId.addEventListener('click', function () {
            memoryIdDialog.close();
          });
        }

        const openCoordinatePicker = function () {
          if (!mapDialog || !latitudeInput || !longitudeInput || !mapLatitudeInput || !mapLongitudeInput || !window.L) {
            return;
          }
          const defaultCoordinates = [20, 0];
          const showSelectedCoordinates = function (latitude, longitude) {
            selectedCoordinates = [latitude, longitude];
            mapLatitudeInput.value = latitude.toFixed(6);
            mapLongitudeInput.value = longitude.toFixed(6);
            if (coordinateMarker) {
              coordinateMarker.setLatLng(selectedCoordinates);
            } else {
              coordinateMarker = L.marker(selectedCoordinates).addTo(coordinateMap);
            }
          };
          const latitude = Number(latitudeInput.value);
          const longitude = Number(longitudeInput.value);
          const hasCoordinates = latitudeInput.value.trim() !== ''
            && longitudeInput.value.trim() !== ''
            && Number.isFinite(latitude)
            && Number.isFinite(longitude);
          mapLatitudeInput.value = hasCoordinates ? latitude : '';
          mapLongitudeInput.value = hasCoordinates ? longitude : '';
          mapDialog.showModal();
          if (!coordinateMap) {
            coordinateMap = L.map('coordinate-map').setView(hasCoordinates ? [latitude, longitude] : defaultCoordinates, hasCoordinates ? 12 : 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '&copy; OpenStreetMap contributors',
            }).addTo(coordinateMap);
            coordinateMap.on('click', function (event) {
              showSelectedCoordinates(event.latlng.lat, event.latlng.lng);
            });
          } else {
            coordinateMap.setView(hasCoordinates ? [latitude, longitude] : defaultCoordinates, hasCoordinates ? 12 : 2);
          }
          if (hasCoordinates) {
            showSelectedCoordinates(latitude, longitude);
          } else {
            selectedCoordinates = null;
            if (coordinateMarker) {
              coordinateMap.removeLayer(coordinateMarker);
              coordinateMarker = null;
            }
          }
          coordinateMap.invalidateSize();
        };

        if (mapDialog && latitudeInput && longitudeInput && mapLatitudeInput && mapLongitudeInput && window.L) {
          const updateMarkerFromInputs = function () {
            const latitude = Number(mapLatitudeInput.value);
            const longitude = Number(mapLongitudeInput.value);
            const hasCoordinates = mapLatitudeInput.value.trim() !== ''
              && mapLongitudeInput.value.trim() !== ''
              && Number.isFinite(latitude)
              && Number.isFinite(longitude);
            if (hasCoordinates) {
              selectedCoordinates = [latitude, longitude];
              if (coordinateMap) {
                coordinateMap.setView(selectedCoordinates, 12);
                if (coordinateMarker) {
                  coordinateMarker.setLatLng(selectedCoordinates);
                } else {
                  coordinateMarker = L.marker(selectedCoordinates).addTo(coordinateMap);
                }
              }
            }
          };
          mapLatitudeInput.addEventListener('change', updateMarkerFromInputs);
          mapLongitudeInput.addEventListener('change', updateMarkerFromInputs);
          cancelMapPicker.addEventListener('click', function () {
            mapDialog.close();
          });
          addMapCoordinates.addEventListener('click', function () {
            latitudeInput.value = mapLatitudeInput.value;
            longitudeInput.value = mapLongitudeInput.value;
            memoryMetadataForm.submit();
          });
        }

        if (showMemoriesBtn && showChosBtn && memoriesPanel && chosPanel && tagsPanel) {
          selectList = function (target) {
            const showMemories = target === 'memories';
            const showChos = target === 'chos';
            const showTags = target === 'tags';
            memoriesPanel.classList.toggle('hidden', !showMemories);
            chosPanel.classList.toggle('hidden', !showChos);
            tagsPanel.classList.toggle('hidden', !showTags);
            showMemoriesBtn.classList.toggle('active', showMemories || showTags);
            showChosBtn.classList.toggle('active', showChos);
          };
          showMemoriesBtn.addEventListener('click', function () { selectList('memories'); });
          showChosBtn.addEventListener('click', function () { selectList('chos'); });
          {% if panel == 'chos' or focus_cho %}
          selectList('chos');
          {% elif selected_memory %}
          selectList('tags');
          {% else %}
          selectList('memories');
          {% endif %}
        }

        if (showMemoriesBtn && showChosBtn && showMetadataBtn) {
          const setVisualization = function (activeButton) {
            [showMemoriesBtn, showChosBtn, showMetadataBtn].forEach(function (button) {
              button.classList.toggle('active', button === activeButton);
            });
          };
          {% if is_metadata_management %}
          setVisualization(showMetadataBtn);
          showMemoriesBtn.addEventListener('click', function () { setVisualization(showMemoriesBtn); window.location.href = '{% if memories %}/?memory_id={{ memories[0].id }}{% else %}/{% endif %}'; });
          showChosBtn.addEventListener('click', function () { setVisualization(showChosBtn); window.location.href = '{% if chos %}/?focus_cho={{ chos[0].custom_id or chos[0].id }}{% else %}/{% endif %}'; });
          {% else %}
          showMemoriesBtn.addEventListener('click', function () { setVisualization(showMemoriesBtn); selectList('memories'); });
          showChosBtn.addEventListener('click', function () { setVisualization(showChosBtn); selectList('chos'); });
          showMetadataBtn.addEventListener('click', function () { setVisualization(showMetadataBtn); });
          {% endif %}
        }

        if (choTagFilter && choTagItems.length) {
          const choValues = Array.from(new Set(choTagItems.map(function (item) {
            return item.getAttribute('data-cho-id') || '';
          }).filter(function (value) { return value; }))).sort();
          choValues.forEach(function (value) {
            const option = document.createElement('option');
            option.value = value;
            const item = choTagItems.find(function (tagItem) {
              return tagItem.getAttribute('data-cho-id') === value;
            });
            option.textContent = item ? (item.getAttribute('data-cho-label') || value) : value;
            choTagFilter.appendChild(option);
          });

          const applyChoTagFilter = function () {
            const selectedCho = (choTagFilter.value || '').trim();
            let visibleCount = 0;
            choTagItems.forEach(function (item) {
              const itemCho = (item.getAttribute('data-cho-id') || '').trim();
              const visible = !selectedCho || selectedCho === itemCho;
              item.classList.toggle('hidden', !visible);
              if (visible) {
                visibleCount += 1;
              }
            });
            if (choTagCount) {
              choTagCount.textContent = visibleCount + ' / ' + choTagItems.length;
            }
          };

          choTagFilter.addEventListener('change', applyChoTagFilter);
          choTagFilter.value = initialChoTagFilter;
          applyChoTagFilter();
        } else if (choTagFilter && choTagsList && choTagsList.textContent && choTagsList.textContent.includes('No object metadata')) {
          choTagFilter.disabled = true;
          if (choTagCount) {
            choTagCount.textContent = '0 shown / 0 total';
          }
        }

        if (memoryMetadataForm) {
          memoryMetadataForm.addEventListener('submit', function (event) {
            saveTextScrollState();
            const deleteInputs = Array.from(memoryMetadataForm.querySelectorAll('input[type="checkbox"][name^="delete_"]'));
            const hasDeletion = deleteInputs.some((input) => input.checked);
            const submitter = event.submitter;
            const explicitRemove = submitter && submitter.name === 'remove_selected';
            if ((hasDeletion || explicitRemove) && !window.confirm('Confirm removal of selected metadata tags?')) {
              event.preventDefault();
            }
          });
        }

        function applyTransform() {
          if (graphContent) {
            graphContent.setAttribute('transform', `translate(${panX} ${panY}) scale(${zoomLevel})`);
          }
        }

        if (svg && graphContent) {
          const updateZoom = (factor) => {
            zoomLevel = Math.max(0.7, Math.min(2.4, zoomLevel * factor));
            applyTransform();
          };

          if (zoomInButton) {
            zoomInButton.addEventListener('click', function () { updateZoom(1.15); });
          }
          if (zoomOutButton) {
            zoomOutButton.addEventListener('click', function () { updateZoom(0.85); });
          }
          if (resetButton) {
            resetButton.addEventListener('click', function () {
              zoomLevel = 1;
              panX = 0;
              panY = 0;
              setHoverValue('Hover object or metadata nodes to inspect values.');
              applyTransform();
            });
          }

          svg.addEventListener('wheel', function (event) {
            event.preventDefault();
            if (event.deltaY < 0) {
              updateZoom(1.05);
            } else {
              updateZoom(0.95);
            }
          }, { passive: false });

          svg.addEventListener('mousedown', function (event) {
            if (event.target.tagName === 'svg' || event.target.tagName === 'circle' || event.target.tagName === 'text') {
              isDragging = true;
              svg.classList.add('dragging');
              startX = event.clientX;
              startY = event.clientY;
            }
          });
          window.addEventListener('mousemove', function (event) {
            if (!isDragging) {
              return;
            }
            panX += event.clientX - startX;
            panY += event.clientY - startY;
            startX = event.clientX;
            startY = event.clientY;
            applyTransform();
          });
          window.addEventListener('mouseup', function () {
            isDragging = false;
            svg.classList.remove('dragging');
          });

          const metadataNodes = Array.from(document.querySelectorAll('.graph-node[data-node-type="memory_metadata"], .graph-node[data-node-type="cho_metadata"]'));
          const metadataLabels = Array.from(document.querySelectorAll('.graph-metadata-label[data-node-type="memory_metadata"], .graph-metadata-label[data-node-type="cho_metadata"]'));
          const allNodeCircles = Array.from(document.querySelectorAll('.graph-node[data-node-id]'));
          const allNodeLabels = Array.from(document.querySelectorAll('.label[data-node-id]'));
          const edgeLines = Array.from(document.querySelectorAll('line[data-from-id][data-to-id]'));
          const nodeCircleById = new Map(allNodeCircles.map((node) => [node.getAttribute('data-node-id') || '', node]));
          const nodeLabelById = new Map(allNodeLabels.map((node) => [node.getAttribute('data-node-id') || '', node]));
          const originalYById = new Map(allNodeCircles.map((node) => [node.getAttribute('data-node-id') || '', parseFloat(node.getAttribute('cy') || '0')]));
          const setHoverValue = (text) => {
            if (hoverValueBox) {
              hoverValueBox.textContent = text || 'No metadata details available.';
            }
          };
          const setNodeY = (nodeId, y) => {
            const circle = nodeCircleById.get(nodeId);
            if (circle) {
              circle.setAttribute('cy', String(y));
            }
            const label = nodeLabelById.get(nodeId);
            if (label) {
              label.setAttribute('y', String(y + 6));
            }
          };
          const updateEdges = () => {
            edgeLines.forEach((line) => {
              const fromId = line.getAttribute('data-from-id') || '';
              const toId = line.getAttribute('data-to-id') || '';
              const fromNode = nodeCircleById.get(fromId);
              const toNode = nodeCircleById.get(toId);
              if (!fromNode || !toNode) {
                return;
              }
              line.setAttribute('x1', fromNode.getAttribute('cx') || '0');
              line.setAttribute('y1', fromNode.getAttribute('cy') || '0');
              line.setAttribute('x2', toNode.getAttribute('cx') || '0');
              line.setAttribute('y2', toNode.getAttribute('cy') || '0');
              const collapsed = fromNode.classList.contains('metadata-collapsed') || toNode.classList.contains('metadata-collapsed');
              line.classList.toggle('edge-collapsed', collapsed);
            });
          };
          const compactLayout = () => {
            const choNodes = allNodeCircles
              .filter((node) => node.getAttribute('data-node-type') === 'cho')
              .sort((a, b) => (originalYById.get(a.getAttribute('data-node-id') || '') || 0) - (originalYById.get(b.getAttribute('data-node-id') || '') || 0));
            let cursorY = 140;
            const rowGap = 64;
            choNodes.forEach((choNode) => {
              const choId = choNode.getAttribute('data-node-id') || '';
              const choMetadata = metadataNodes
                .filter((node) => (node.getAttribute('data-parent-id') || '') === choId)
                .sort((a, b) => (originalYById.get(a.getAttribute('data-node-id') || '') || 0) - (originalYById.get(b.getAttribute('data-node-id') || '') || 0));
              const visibleMetadata = choMetadata.filter((node) => !node.classList.contains('metadata-collapsed'));
              const visibleCount = visibleMetadata.length;
              const choY = visibleCount > 0 ? cursorY + ((visibleCount - 1) * rowGap) / 2 : cursorY + 35;
              setNodeY(choId, choY);
              visibleMetadata.forEach((node, index) => {
                const nodeId = node.getAttribute('data-node-id') || '';
                setNodeY(nodeId, cursorY + index * rowGap);
              });
              const bandHeight = visibleCount > 0 ? Math.max(170, visibleCount * rowGap + 55) : 110;
              cursorY += bandHeight;
            });
            updateEdges();
          };
          const initiallyVisibleMetadataNode = metadataNodes.find((node) => node.classList.contains('metadata-visible'));
          if (initiallyVisibleMetadataNode) {
            setHoverValue(initiallyVisibleMetadataNode.getAttribute('data-details'));
          }

          const scrollToMetadataHighlight = (node) => {
            if (!source || !node || !node.matches('.graph-node[data-node-type="cho_metadata"]')) {
              return;
            }
            const field = (node.getAttribute('data-metadata-field') || '').split('@')[0];
            const value = (node.getAttribute('data-metadata-value') || '').trim();
            const target = Array.from(source.querySelectorAll('.highlight'))
              .find((span) => (span.getAttribute('title') || '') === field && (span.textContent || '').trim() === value);
            if (!target) {
              return;
            }
            const sourceBounds = source.getBoundingClientRect();
            const targetBounds = target.getBoundingClientRect();
            source.scrollTo({
              top: source.scrollTop + targetBounds.top - sourceBounds.top - (source.clientHeight - targetBounds.height) / 2,
              behavior: 'smooth',
            });
          };

          const selectMetadataTag = (node) => {
            if (!node || !node.matches('.graph-node[data-node-type="cho_metadata"]')) {
              return;
            }
            const field = node.getAttribute('data-metadata-field') || '';
            const value = (node.getAttribute('data-metadata-value') || '').trim();
            const tag = Array.from(document.querySelectorAll('.cho-tag-link[data-metadata-field]'))
              .find((item) => item.getAttribute('data-metadata-field') === field && (item.getAttribute('data-metadata-value') || '').trim() === value);
            if (!tag) {
              return;
            }
            const checkbox = tag.closest('.tag-selector')?.querySelector('input[type="checkbox"]');
            if (!checkbox) {
              return;
            }
            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
          };

          const nodeElements = Array.from(document.querySelectorAll('.graph-node'));
          nodeElements.forEach((node) => {
            node.addEventListener('mouseenter', function () {
              setHoverValue(node.getAttribute('data-details'));
              scrollToMetadataHighlight(node);
            });
            node.addEventListener('click', function (event) {
              const nodeType = node.getAttribute('data-node-type');
              if (nodeType === 'cho_metadata') {
                event.preventDefault();
                selectMetadataTag(node);
              }
              if (nodeType === 'cho' || nodeType === 'memory') {
                setHoverValue(node.getAttribute('data-details'));
              }
            });
          });

          metadataNodes.forEach((node) => {
            node.addEventListener('mouseenter', function () {
              setHoverValue(node.getAttribute('data-details'));
            });
            node.addEventListener('click', function (event) {
              event.preventDefault();
              setHoverValue(node.getAttribute('data-details'));
            });
          });

          compactLayout();
        }
      });
    </script>
{{ close_on_unload_script }}
  </body>
</html>
"""

HTML_TEMPLATE = HTML_TEMPLATE.replace("{{ close_on_unload_script }}", CLOSE_ON_UNLOAD_SCRIPT)

METADATA_SPACES_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Medatata Spaces Management</title>
    <style>
      :root { --ink: #17212b; --muted: #4f6472; --line: #b8c7d1; --surface: #ffffff; --wash: #eef3f6; --brand: #003b5c; --accent: #e69f00; }
      * { box-sizing: border-box; }
      body { margin: 0; color: var(--ink); font-family: "Avenir Next", "Segoe UI", sans-serif; background: var(--wash); }
      .page { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 34px 0 48px; }
      .topbar { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 24px; }
      h1, h2, h3, p { margin-top: 0; }
      h1 { margin-bottom: 6px; font-size: clamp(1.6rem, 3vw, 2.35rem); }
      h2 { margin-bottom: 6px; font-size: 1.15rem; }
      .intro { max-width: 680px; color: var(--muted); margin-bottom: 0; }
      .back-link { color: var(--brand); font-weight: 700; }
      .layout { display: grid; grid-template-columns: minmax(220px, .7fr) minmax(0, 1.3fr); gap: 18px; align-items: start; }
      .embedded-page .layout { grid-template-columns: minmax(0, 1fr); }
      .embedded-page .panel { width: 100%; min-height: calc(100vh - 170px); }
      .panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 10px 26px rgba(23, 33, 43, .08); padding: 18px; }
      .scheme-list { display: grid; gap: 8px; margin: 14px 0 0; }
      .scheme-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 10px; border: 1px solid var(--line); border-radius: 6px; background: #f8fbfc; }
      .scheme-row strong { display: block; }
      .scheme-row small { color: var(--muted); }
      .scheme-actions { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
      .button, button { border: 0; border-radius: 5px; padding: 8px 11px; color: white; background: var(--brand); cursor: pointer; font: inherit; font-size: .86rem; font-weight: 700; text-decoration: none; }
      .button.secondary, button.secondary { color: var(--ink); background: #dbe8ed; }
      .button.accent, button.accent { background: var(--accent); }
      label { display: block; margin: 12px 0 5px; color: var(--muted); font-size: .8rem; font-weight: 700; }
      input, textarea { width: 100%; border: 1px solid #c4d1d9; border-radius: 5px; padding: 9px; color: var(--ink); background: white; font: inherit; }
      textarea { min-height: 74px; resize: vertical; }
      .form-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0 12px; }
      .form-grid .full { grid-column: 1 / -1; }
      .field-head, .field-row { display: grid; grid-template-columns: minmax(130px, .8fr) minmax(180px, 1.2fr) auto; gap: 8px; align-items: end; }
      .field-head { margin-top: 16px; color: var(--muted); font-size: .8rem; font-weight: 700; }
      .field-row { margin-top: 6px; }
      .field-row label { margin-top: 0; }
      .remove-field { background: #b45309; padding-inline: 10px; }
      .form-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 18px; }
      .notice { margin-bottom: 16px; padding: 10px 12px; border-radius: 5px; background: #dcfce7; color: #166534; }
      .error { background: #fee2e2; color: #991b1b; }
      .import-box { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--line); }
      @media (max-width: 760px) { .topbar, .layout { display: block; } .back-link { display: inline-block; margin-top: 12px; } .panel + .panel { margin-top: 16px; } .form-grid, .metadata-import-form { display: block; } .metadata-import-form input[type="file"] { margin-bottom: 6px; } .metadata-import-form button { width: 100%; } .field-head { display: none; } .field-row { grid-template-columns: 1fr; padding: 10px 0; border-bottom: 1px solid var(--line); } }
    </style>
  </head>
  <body>
    <main class="page{% if embedded %} embedded-page{% endif %}">
      {% if notice %}<div class="notice">{{ notice }}</div>{% endif %}
      {% if error %}<div class="notice error">{{ error }}</div>{% endif %}
      <div class="layout">
        {% if not embedded %}
        <section class="panel">
          <h2>Existing Metadata Spaces</h2>
          <p class="intro">Download a scheme as CSV or load it into the editor.</p>
          <div class="scheme-list">
            {% for space in spaces %}
            <div class="scheme-row">
              <div><strong>{{ space.name }}</strong><small>{{ space.description }}</small></div>
              <div class="scheme-actions"><a class="button secondary" href="/metadata-spaces/{{ space.name }}.csv">Download</a><a class="button" href="/metadata-spaces?edit={{ space.name }}">Edit</a></div>
            </div>
            {% endfor %}
          </div>
          <div class="import-box">
            <h2>Import CSV</h2>
            <form class="metadata-import-form" action="/metadata-spaces/import" method="post" enctype="multipart/form-data">
              <input type="file" name="file" accept=".csv,text/csv" required>
              <div class="form-actions"><button class="accent" type="submit">Import Metadata Space</button></div>
            </form>
          </div>
        </section>
        {% endif %}
        <section class="panel">
          <form id="metadata-space-form" method="post" action="/metadata-spaces"{% if embedded %} target="_top"{% endif %}>
            <input type="hidden" name="original_name" value="{{ editing.name if editing else "" }}">
            <input type="hidden" name="replace" value="1">
            <div class="form-grid">
              <div><label for="space-name">Scheme name</label><input id="space-name" name="name" value="{{ editing.name if editing else "" }}" required></div>
              <div><label for="space-author">Author</label><input id="space-author" name="author" value="{{ editing.author if editing else "" }}" required></div>
              <div><label for="space-date">Date of update</label><input id="space-date" name="updated_at" value="{{ editing.updated_at if editing else "" }}" required></div>
              <div class="full"><label for="space-description">Description</label><textarea id="space-description" name="description" required>{{ editing.description if editing else "" }}</textarea></div>
            </div>
            <div class="field-head"><span>Field</span><span>Description</span><span></span></div>
            <div id="field-list">
              {% set form_fields = editing.fields if editing else [{"name": "", "description": ""}] %}
              {% for field in form_fields %}
              <div class="field-row"><input name="field_name" value="{{ field.name }}" placeholder="Field name" required><input name="field_description" value="{{ field.description }}" placeholder="Field description" required><button class="remove-field" type="button" title="Remove field">Remove</button></div>
              {% endfor %}
            </div>
            <div class="form-actions"><button class="secondary" id="add-field" type="button">Add field</button><button type="submit">Save Metadata Space</button></div>
          </form>
        </section>
      </div>
    </main>
    <script>
      const fieldList = document.getElementById('field-list');
      const addField = document.getElementById('add-field');
      const metadataSpaceForm = document.getElementById('metadata-space-form');
      function bindRemove(button) { button.addEventListener('click', function () { if (fieldList.children.length > 1) button.parentElement.remove(); }); }
      document.querySelectorAll('.remove-field').forEach(bindRemove);
      addField.addEventListener('click', function () { const row = document.createElement('div'); row.className = 'field-row'; row.innerHTML = '<input name="field_name" placeholder="Field name" required><input name="field_description" placeholder="Field description" required><button class="remove-field" type="button" title="Remove field">Remove</button>'; fieldList.appendChild(row); bindRemove(row.querySelector('.remove-field')); });
      if (metadataSpaceForm && window.top !== window) {
        metadataSpaceForm.addEventListener('submit', function (event) {
          event.preventDefault();
          const action = new URL(metadataSpaceForm.action, window.location.href);
          action.searchParams.set('embedded', '1');
          fetch(action, { method: 'POST', body: new FormData(metadataSpaceForm), redirect: 'follow' })
            .then(function (response) { window.top.location.href = response.url; })
            .catch(function () { window.top.location.href = '/?workspace=metadata_spaces'; });
        });
      }
    </script>
{{ close_on_unload_script }}
  </body>
</html>
"""

METADATA_SPACES_TEMPLATE = METADATA_SPACES_TEMPLATE.replace("{{ close_on_unload_script }}", CLOSE_ON_UNLOAD_SCRIPT)

SEARCH_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Search memories</title>
    <style>
      body { font-family: "Avenir Next", "Segoe UI", sans-serif; margin: 0; background: #eef3f6; color: #17212b; }
      .wrap { max-width: 980px; margin: 32px auto; padding: 24px; }
      .card { background: white; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
      form input { width: 100%; margin-bottom: 10px; padding: 8px; box-sizing: border-box; }
      button { padding: 6px 10px; border: 0; border-radius: 4px; background: #003b5c; color: white; cursor: pointer; font: inherit; font-size: 12px; font-weight: 700; }
      a { color: #0f5b78; text-decoration: none; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #e5e7eb; }
      .snippet { color: #475569; }
      .pagination { margin-top: 10px; display: flex; gap: 12px; align-items: center; }
      .back-btn { display: inline-block; padding: 6px 10px; border-radius: 4px; background: #003b5c; color: white; font-size: 12px; font-weight: 700; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Search memories</h1>
        <p>This mirrors the desktop search flow across memory text.</p>
      </div>
      <div class="card">
        <form method="get" action="/search">
          <label>Search term</label>
          <input name="q" value="{{ q }}" placeholder="Type a word or phrase">
          <button type="submit">Search</button>
        </form>
      </div>
      {% if searched %}
      <div class="card">
        <h2>Results ({{ total_results }})</h2>
        <table>
          <thead><tr><th>Memory</th><th>Title</th><th>Snippet</th></tr></thead>
          <tbody>
            {% for row in result_rows %}
            <tr>
              <td><a href="/?memory_id={{ row.id }}">{{ row.custom_id or row.id }}</a></td>
              <td>{{ row.title or ('Memory ' ~ row.id) }}</td>
              <td class="snippet">{{ row.snippet }}</td>
            </tr>
            {% else %}
            <tr><td colspan="3">No matches found.</td></tr>
            {% endfor %}
          </tbody>
        </table>
        {% if total_pages > 1 %}
        <div class="pagination">
          {% if page > 1 %}
          <a href="/search?q={{ q }}&page={{ page - 1 }}">Previous</a>
          {% endif %}
          <span>Page {{ page }} of {{ total_pages }}</span>
          {% if page < total_pages %}
          <a href="/search?q={{ q }}&page={{ page + 1 }}">Next</a>
          {% endif %}
        </div>
        {% endif %}
      </div>
      {% endif %}
    </div>
{{ close_on_unload_script }}
  </body>
</html>
"""

SEARCH_TEMPLATE = SEARCH_TEMPLATE.replace("{{ close_on_unload_script }}", CLOSE_ON_UNLOAD_SCRIPT)

COMPARE_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Object metadata report</title>
    <style>
      body { font-family: "Avenir Next", "Segoe UI", sans-serif; margin: 0; background: #eef3f6; color: #17212b; }
      .wrap { max-width: 980px; margin: 32px auto; padding: 24px; }
      .card { background: white; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
      form select { width: 100%; margin-bottom: 10px; padding: 8px; box-sizing: border-box; }
      button { padding: 6px 10px; border: 0; border-radius: 4px; background: #003b5c; color: white; cursor: pointer; font: inherit; font-size: 12px; font-weight: 700; }
      a { color: #0f5b78; text-decoration: none; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #e5e7eb; }
      .matrix th:first-child, .matrix td:first-child { min-width: 170px; font-weight: 600; background: #f8fafc; }
      .matrix-wrap { overflow: auto; }
      .back-btn { display: inline-block; padding: 6px 10px; border-radius: 4px; background: #003b5c; color: white; font-size: 12px; font-weight: 700; }
      .field-name { border-bottom: 1px dotted #94a3b8; cursor: help; }
      .field-help { margin-left: 6px; color: #64748b; font-size: 12px; cursor: help; }
      .view-toggle { display: flex; gap: 12px; margin-bottom: 12px; }
      .view-toggle label { display: flex; align-items: center; gap: 4px; }
      .report-section { margin-top: 24px; }
      .report-section h3 { margin-bottom: 8px; }
      .report-table { table-layout: fixed; }
      .report-count { width: 5%; }
      .report-instance { width: 65%; }
      .report-memories { width: 30%; }
      .memory-links a + a::before { content: ", "; color: #64748b; }
      .download-btn { display: inline-block; margin-bottom: 12px; padding: 6px 10px; border-radius: 4px; background: #e69f00; color: #17212b; font-size: 12px; font-weight: 700; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Report by Object</h1>
        <p>Review metadata fields, instances, counts, and related memories for one object.</p>
      </div>
      <div class="card">
        <form method="get" action="{{ '/' if embedded else '/compare' }}"{% if embedded %} target="_top"{% endif %}>
          {% if embedded %}<input type="hidden" name="workspace" value="compare">{% endif %}
          <input type="hidden" name="metadata_space" value="{{ metadata_space.name }}">
          <label>Object</label>
          <select name="cho_id">
            <option value="">Choose object</option>
            {% for cho in chos %}
            <option value="{{ cho.custom_id or cho.id }}" {% if selected_cho == (cho.custom_id or cho.id|string) %}selected{% endif %}>{{ cho.title or cho.custom_id or cho.id }} ({{ cho.custom_id or cho.id }})</option>
            {% endfor %}
          </select>
          <div class="view-toggle">
            <label><input type="radio" name="view" value="matrix" {% if view == 'matrix' %}checked{% endif %}> Memory/Object matrix</label>
            <label><input type="radio" name="view" value="fields" {% if view == 'fields' %}checked{% endif %}> Memory/Field matrix</label>
          </div>
          <button type="submit">Show results</button>
        </form>
      </div>
      {% if view == 'matrix' %}
      <div class="card">
        <h2>Memory / Object matrix</h2>
        <p>Number of metadata tags each memory has for each object. Totals in brackets show the object's or memory's overall annotation count.</p>
        <div class="matrix-wrap">
          <table class="matrix">
            <thead>
              <tr>
                <th>Memory</th>
                {% for column in matrix_cho_columns %}
                <th><a href="/?focus_cho={{ column.key }}">{{ column.label }} [{{ column.total }}]</a></th>
                {% endfor %}
              </tr>
            </thead>
            <tbody>
              {% for row in matrix_memory_rows %}
              <tr>
                <td><a href="/?memory_id={{ row.id }}">{{ row.label }} [{{ row.total }}]</a></td>
                {% for column in matrix_cho_columns %}
                <td>{{ row['values'].get(column.key, 0) }}</td>
                {% endfor %}
              </tr>
              {% else %}
              <tr><td colspan="{{ (matrix_cho_columns|length) + 1 }}">No memories found.</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
      {% elif view == 'fields' %}
      <div class="card">
        <h2>Memory / Field matrix</h2>
        <p>Number of times each metadata field appears within each memory, regardless of object. Totals in brackets show the field's or memory's overall annotation count.</p>
        <div class="matrix-wrap">
          <table class="matrix">
            <thead>
              <tr>
                <th>Memory</th>
                {% for column in matrix_field_columns %}
                <th><span class="field-name" title="{{ field_descriptions.get(column.key, column.label) }}">{{ column.label }}</span> [{{ column.total }}]</th>
                {% endfor %}
              </tr>
            </thead>
            <tbody>
              {% for row in matrix_field_memory_rows %}
              <tr>
                <td><a href="/?memory_id={{ row.id }}">{{ row.label }} [{{ row.total }}]</a></td>
                {% for column in matrix_field_columns %}
                <td>{{ row['values'].get(column.key, 0) }}</td>
                {% endfor %}
              </tr>
              {% else %}
              <tr><td colspan="{{ (matrix_field_columns|length) + 1 }}">No memories found.</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
      {% elif selected_cho %}
      <div class="card">
        <h2>{% if view == 'report' %}Report{% else %}Comparison{% endif %} for object <a href="/?focus_cho={{ selected_cho }}">{{ selected_cho }}</a></h2>
        {% if view == 'report' %}
        <a class="download-btn" href="/compare/report.csv?cho_id={{ selected_cho }}&metadata_space={{ metadata_space.name }}">Download CSV</a>
        {% for section in report_sections %}
        <section class="report-section">
          <h3><span class="field-name" title="{{ field_descriptions.get(section.field, section.field) }}">{{ section.display_field }}</span></h3>
          <table class="report-table">
            <thead><tr><th class="report-count">N</th><th class="report-instance">Instance</th><th class="report-memories">Related memories</th></tr></thead>
            <tbody>
              {% for row in section.rows %}
              <tr>
                <td class="report-count">{{ row.count }}</td>
                <td class="report-instance">{{ row.value }}</td>
                <td class="report-memories memory-links">{% for memory in row.memories %}<a href="/?memory_id={{ memory.id }}&filter_cho={{ selected_cho }}">{{ memory.label }}</a>{% endfor %}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </section>
        {% else %}
        <p>No metadata found for this CHO.</p>
        {% endfor %}
        {% else %}
        <div class="matrix-wrap">
          <table class="matrix">
            <thead>
              <tr>
                <th>Field</th>
                {% for memory in memory_columns %}
                <th><a href="/?memory_id={{ memory.id }}&filter_cho={{ selected_cho }}">{{ memory.label }}</a></th>
                {% endfor %}
              </tr>
            </thead>
            <tbody>
              {% for row in matrix_rows %}
              <tr>
                <td>
                  <span class="field-name" title="{{ field_descriptions.get(row.field, row.field) }}">{{ row.display_field }}</span>
                  <span class="field-help" title="{{ field_descriptions.get(row.field, row.field) }}">i</span>
                </td>
                {% for memory in memory_columns %}
                <td>{{ row['values'].get(memory.id, '—') }}</td>
                {% endfor %}
              </tr>
              {% else %}
              <tr><td colspan="{{ (memory_columns|length) + 1 }}">No metadata found for this CHO.</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
        {% endif %}
      </div>
      {% endif %}
    </div>
{{ close_on_unload_script }}
  </body>
</html>
"""

COMPARE_TEMPLATE = COMPARE_TEMPLATE.replace("{{ close_on_unload_script }}", CLOSE_ON_UNLOAD_SCRIPT)

MAP_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Memory map - CORDHISK</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <style>
      :root { --ink: #17212b; --brand: #003b5c; --surface: #ffffff; --line: #b8c7d1; --bg: #eef3f6; }
      body { font-family: "Avenir Next", "Segoe UI", sans-serif; margin: 0; background: var(--bg); color: var(--ink); }
      .wrap { max-width: 1200px; margin: 0 auto; padding: 24px; }
      .topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
      h1 { margin: 0; font-size: 28px; }
      p { margin: 6px 0 0; color: #475569; }
      a { color: #005b8f; text-decoration: none; }
      .back-link { display: inline-block; padding: 8px 12px; border-radius: 6px; background: var(--brand); color: white; white-space: nowrap; }
      .map { height: min(70vh, 680px); min-height: 420px; border: 1px solid var(--line); }
      .empty { padding: 24px; border: 1px solid var(--line); background: var(--surface); }
      .memory-list { margin: 20px 0 0; padding: 0; list-style: none; columns: 2; }
      .memory-list li { margin: 0 0 8px; break-inside: avoid; }
      .marker-title { font-weight: 700; margin-bottom: 4px; }
      @media (max-width: 700px) { .topbar { align-items: flex-start; flex-direction: column; } .memory-list { columns: 1; } }
    </style>
  </head>
  <body>
    <main class="wrap">
      <div class="topbar">
        <div>
          <h1>Memory map</h1>
          <p>Explore memories with stored WGS84 coordinates.</p>
        </div>
      </div>
      {% if markers %}
      <div id="memory-map" class="map" role="application" aria-label="Map of memories with coordinates"></div>
      <ul class="memory-list">
        {% for marker in markers %}
        <li><a href="/?memory_id={{ marker.id }}">{{ marker.label }} - {{ marker.title }}</a> ({{ marker.latitude }}, {{ marker.longitude }})</li>
        {% endfor %}
      </ul>
      {% else %}
      <div class="empty">No memories with valid coordinates are available yet.</div>
      {% endif %}
    </main>
    {% if markers %}
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
      const markers = {{ markers | tojson }};
      const map = L.map('memory-map');
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);
      const bounds = [];
      markers.forEach(function (memory) {
        const coordinates = [memory.latitude, memory.longitude];
        const popup = document.createElement('div');
        const title = document.createElement('div');
        title.className = 'marker-title';
        title.textContent = memory.label + ' - ' + memory.title;
        const link = document.createElement('a');
        link.href = '/?memory_id=' + encodeURIComponent(memory.id);
        link.textContent = 'Open memory';
        popup.appendChild(title);
        popup.appendChild(link);
        L.marker(coordinates).addTo(map).bindPopup(popup);
        bounds.push(coordinates);
      });
      if (bounds.length === 1) {
        map.setView(bounds[0], 12);
      } else {
        map.fitBounds(bounds, { padding: [32, 32] });
      }
    </script>
    {% endif %}
{{ close_on_unload_script }}
  </body>
</html>
"""

MAP_TEMPLATE = MAP_TEMPLATE.replace("{{ close_on_unload_script }}", CLOSE_ON_UNLOAD_SCRIPT)

IMPORT_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Import memory</title>
    <style>
      body { font-family: "Avenir Next", "Segoe UI", sans-serif; margin: 0; background: #eef3f6; color: #17212b; }
      .wrap { max-width: 760px; margin: 32px auto; padding: 24px; }
      .card { background: white; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
      form input, form textarea { width: 100%; margin-bottom: 10px; padding: 8px; box-sizing: border-box; }
      button { padding: 6px 10px; border: 0; border-radius: 4px; background: #003b5c; color: white; cursor: pointer; font: inherit; font-size: 12px; font-weight: 700; }
      a { color: #0f5b78; text-decoration: none; }
      .status-msg { display: none; }
    </style>
  </head>
  <body>
    <div class="wrap">
      {% if notice_message %}
      <div class="status-msg" aria-hidden="true">{{ notice_message }}</div>
      {% endif %}
      <div class="card">
        <h1>Import a new memory</h1>
        <p>Upload a text file and assign the initial memory metadata before the memory becomes available in the web app.</p>
      </div>
      <div class="card">
        <form action="/memories/import" method="post" enctype="multipart/form-data"{% if embedded and import_ready %} target="_top"{% endif %}>
          {% if embedded %}<input type="hidden" name="embedded" value="1">{% endif %}
          {% if not import_ready %}
          <input type="hidden" name="stage" value="prepare">
          <label>Text file</label>
          <input name="file" type="file" accept=".txt,text/plain" required>
          <label>ID (optional)</label>
          <input name="id" value="{{ suggested_id or '' }}" placeholder="e.g. 005">
          <button type="submit">Load metadata</button>
          {% else %}
          <input type="hidden" name="stage" value="confirm">
          <input type="hidden" name="temp_path" value="{{ temp_path }}">
          <p><strong>Detected metadata:</strong> {{ detected_count }} existing fields</p>
          <label>ID</label>
          <input name="id" value="{{ suggested_id or '' }}" placeholder="e.g. 005" required>
          <label>Title</label>
          <input name="dc:title" value="{{ form_metadata.get('dc:title', '') }}" placeholder="Memory title">
          <label>Creator</label>
          <input name="dc:creator" value="{{ form_metadata.get('dc:creator', '') }}" placeholder="Creator">
          <label>Date</label>
          <input name="dc:date" value="{{ form_metadata.get('dc:date', '') }}" placeholder="Date">
          <label>Subject</label>
          <input name="dc:subject" value="{{ form_metadata.get('dc:subject', '') }}" placeholder="Subject">
          <label>Description</label>
          <textarea name="dc:description" placeholder="Description">{{ form_metadata.get('dc:description', '') }}</textarea>
          <label>License</label>
          <select name="dc:license">
            <option value="">Select a license</option>
            {% for license_option in memory_license_options %}
            <option value="{{ license_option }}" {% if form_metadata.get('dc:license', '') == license_option %}selected{% endif %}>{{ license_option }}</option>
            {% endfor %}
          </select>
          <button type="submit">Import memory</button>
          {% endif %}
        </form>
      </div>
    </div>
{{ close_on_unload_script }}
  </body>
</html>
"""

IMPORT_TEMPLATE = IMPORT_TEMPLATE.replace("{{ close_on_unload_script }}", CLOSE_ON_UNLOAD_SCRIPT)