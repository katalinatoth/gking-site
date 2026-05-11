/*!
 * Gary King Chat Widget — embeddable chat launcher
 *
 * Usage:
 *   <script src="https://your-host/gking-chat-widget.js"
 *           data-api-url="https://your-api.example.com/chat"
 *           data-bot-id="gking"
 *           data-bot-name="Gary King's AI Avatar"
 *           data-welcome-message="Hello, I'm Gary King..."
 *           data-avatar-label="GK"
 *           data-input-placeholder="Ask me about my research..."
 *           defer></script>
 *
 * Or configure via window.GKingChatConfig before loading the script:
 *   <script>
 *     window.GKingChatConfig = { apiUrl: "https://your-api.example.com/chat" };
 *   </script>
 *   <script src="https://your-host/gking-chat-widget.js" defer></script>
 *
 * Programmatic control after load:
 *   window.GKingChat.open();
 *   window.GKingChat.close();
 *   window.GKingChat.toggle();
 *   window.GKingChat.reset();
 */
(function () {
  "use strict";

  var WIDGET_VERSION = "1.1.0";

  // Capture currentScript synchronously (null-safe inside async callbacks).
  var scriptEl = document.currentScript;

  function uuid() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      var v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function readConfig() {
    var userConfig = window.GKingChatConfig || {};
    var dataConfig = {};
    if (scriptEl && scriptEl.dataset) {
      var d = scriptEl.dataset;
      if (d.apiUrl) dataConfig.apiUrl = d.apiUrl;
      if (d.feedbackUrl) dataConfig.feedbackUrl = d.feedbackUrl;
      if (d.botId) dataConfig.botId = d.botId;
      if (d.botName) dataConfig.botName = d.botName;
      if (d.welcomeMessage) dataConfig.welcomeMessage = d.welcomeMessage;
      if (d.avatarLabel) dataConfig.avatarLabel = d.avatarLabel;
      if (d.inputPlaceholder) dataConfig.inputPlaceholder = d.inputPlaceholder;
    }
    var defaults = {
      apiUrl: "",
      feedbackUrl: "",
      botId: "gking",
      botName: "Gary King's AI Avatar",
      welcomeMessage:
        "This is Gary King's AI chatbot. How can I help?",
      avatarLabel: "GK",
      inputPlaceholder: "Ask me about my research..."
    };
    return Object.assign({}, defaults, userConfig, dataConfig);
  }

  function deriveFeedbackUrl(cfg) {
    if (cfg.feedbackUrl) return cfg.feedbackUrl;
    if (!cfg.apiUrl) return "";
    if (/\/chat\/?$/.test(cfg.apiUrl)) return cfg.apiUrl.replace(/\/chat(\/?)$/, "/feedback$1");
    return cfg.apiUrl.replace(/\/?$/, "") + "/feedback";
  }

  var FONT = "'Helvetica Neue', Arial, sans-serif";
  var CSS = [
    // Match the chatbot (static/index.html + Next.js `antialiased` body) by
    // pinning the same font stack AND the same smoothing hints inside the
    // shadow DOM. `all: initial` strips inheritance, so re-declare smoothing
    // here or fonts render slightly bolder than the chatbot on macOS.
    ":host { all: initial; font-family: " + FONT + "; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility; }",
    // Force the font on every descendant — UA stylesheets reset font-family on form controls.
    ":host, :host *, button, input, textarea, select { font-family: " + FONT + " !important; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }",
    "* { box-sizing: border-box; }",
    ".btn {",
    "  position: fixed; right: 24px; bottom: 24px;",
    "  width: 60px; height: 60px; border-radius: 50%;",
    "  border: none; cursor: pointer;",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  color: #fff;",
    "  box-shadow: 0 8px 24px rgba(88,118,169,0.35);",
    "  display: flex; align-items: center; justify-content: center;",
    "  z-index: 2147483000;",
    "  transition: transform 0.15s ease;",
    "}",
    ".btn:active { transform: scale(0.94); }",
    ".panel {",
    "  position: fixed; right: 24px; bottom: 100px;",
    "  width: min(380px, calc(100vw - 32px));",
    "  height: min(560px, calc(100vh - 140px));",
    "  background: #fff;",
    "  border-radius: 16px;",
    "  border: 1px solid #dde8f5;",
    "  box-shadow: 0 12px 48px rgba(88,118,169,0.25);",
    "  display: flex; flex-direction: column; overflow: hidden;",
    "  z-index: 2147483001;",
    "  color: #3a4a6b;",
    "}",
    ".panel[hidden] { display: none; }",
    ".header {",
    "  padding: 14px 16px;",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  color: #fff;",
    "  display: flex; align-items: center; gap: 10px;",
    "}",
    ".header .avatar {",
    "  width: 34px; height: 34px; border-radius: 50%;",
    "  background: rgba(255,255,255,0.18);",
    "  border: 1px solid rgba(255,255,255,0.35);",
    "  display: flex; align-items: center; justify-content: center;",
    "  font-size: 12px; font-weight: 700;",
    "}",
    ".header .title { flex: 1; min-width: 0; }",
    ".header .name { font-size: 15px; font-weight: 700; line-height: 1.2; }",
    ".header .status { font-size: 11px; opacity: 0.85; margin-top: 2px; }",
    ".header .status-dot {",
    "  display: inline-block; width: 6px; height: 6px; border-radius: 50%;",
    "  background: #1bbc9d; margin-right: 6px; vertical-align: middle;",
    "}",
    ".header .close {",
    "  background: transparent; border: none; color: #fff;",
    "  opacity: 0.9; cursor: pointer; padding: 4px; display: flex;",
    "}",
    ".messages {",
    "  flex: 1; overflow-y: auto;",
    "  padding: 14px 14px 6px;",
    "  display: flex; flex-direction: column; gap: 12px;",
    "  background: #f7f9fc;",
    "}",
    ".msg { display: flex; gap: 8px; align-items: flex-start; }",
    ".msg.user { justify-content: flex-end; }",
    ".avatar-sm {",
    "  width: 26px; height: 26px; border-radius: 50%;",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  color: #fff;",
    "  display: flex; align-items: center; justify-content: center;",
    "  font-size: 10px; font-weight: 700; flex-shrink: 0; margin-top: 2px;",
    "}",
    ".bubble {",
    "  max-width: 82%;",
    "  padding: 9px 12px;",
    "  font-size: 14px; line-height: 1.85;",
    "  font-family: " + FONT + ";",
    "  word-break: break-word;",
    "  white-space: pre-wrap;",
    "}",
    ".msg.user .bubble {",
    "  border-radius: 14px 14px 4px 14px;",
    "  background: #5876a9; color: #fff;",
    "}",
    ".msg.bot .bubble {",
    "  border-radius: 14px 14px 14px 4px;",
    "  background: #fff; color: #3a4a6b;",
    "  border: 1px solid #dde8f5;",
    "}",
    ".bubble strong { color: #5876a9; font-weight: 700; }",
    ".bubble code {",
    "  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;",
    "  background: #f7f9fc; border: 1px solid #dde8f5; border-radius: 4px;",
    "  padding: 1px 5px; font-size: 0.92em; color: #5876a9;",
    "}",
    ".bubble a { color: #5876a9; text-decoration: underline; }",
    ".typing {",
    "  background: #fff; border: 1px solid #dde8f5;",
    "  border-radius: 14px 14px 14px 4px;",
    "  padding: 10px 14px; display: flex; gap: 4px;",
    "}",
    ".typing span {",
    "  width: 6px; height: 6px; border-radius: 50%;",
    "  background: #5876a9; animation: gkingPulse 1.2s infinite;",
    "}",
    ".typing span:nth-child(2) { animation-delay: 120ms; }",
    ".typing span:nth-child(3) { animation-delay: 240ms; }",
    "@keyframes gkingPulse {",
    "  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }",
    "  30% { transform: translateY(-3px); opacity: 1; }",
    "}",
    ".input-row {",
    "  padding: 12px; background: #fff;",
    "  border-top: 1px solid #dde8f5;",
    "  display: flex; gap: 8px; align-items: flex-end;",
    "}",
    ".input-row textarea {",
    "  flex: 1; resize: none;",
    "  border: 1px solid #dde8f5; border-radius: 10px;",
    "  padding: 9px 12px; font-size: 14px;",
    "  font-family: 'Helvetica Neue', Arial, sans-serif;",
    "  color: #3a4a6b; outline: none;",
    "  max-height: 120px; line-height: 1.4;",
    "}",
    ".input-row .send {",
    "  width: 38px; height: 38px; border-radius: 50%; border: none;",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  color: #fff; cursor: pointer;",
    "  display: flex; align-items: center; justify-content: center; flex-shrink: 0;",
    "}",
    ".input-row .send:disabled { background: #b0bfd4; cursor: not-allowed; }",
    ".input-row .send.stop { background: #b0bfd4; cursor: pointer; }",
    ".input-row .send.stop:hover { background: #9aacc4; }",
    ".feedback-row {",
    "  display: flex; gap: 4px; align-items: center;",
    "  margin: 4px 0 0 34px;",
    "}",
    ".feedback-btn {",
    "  background: transparent; border: none; cursor: pointer;",
    "  padding: 4px; border-radius: 6px; line-height: 0;",
    "  color: #8a9ab8; transition: background 0.15s ease, color 0.15s ease;",
    "}",
    ".feedback-btn.up:hover:not(:disabled) { background: #e6f7f0; color: #2bb673; }",
    ".feedback-btn.down:hover:not(:disabled) { background: #fdeceb; color: #e15554; }",
    ".feedback-btn.up.active { color: #2bb673; }",
    ".feedback-btn.down.active { color: #e15554; }",
    ".feedback-btn:disabled { cursor: default; }",
    ".feedback-btn.active:disabled { opacity: 1; }",
    ".feedback-thanks { font-size: 11px; color: #8a9ab8; margin-left: 4px; }",
    ".feedback-comment {",
    "  margin: 6px 0 0 34px;",
    "  display: flex; flex-direction: column; gap: 6px;",
    "  background: #fff; border: 1px solid #dde8f5; border-radius: 10px;",
    "  padding: 8px;",
    "}",
    ".feedback-comment textarea {",
    "  border: none; outline: none; resize: vertical;",
    "  min-height: 48px; max-height: 120px;",
    "  font-family: 'Helvetica Neue', Arial, sans-serif;",
    "  font-size: 13px; color: #3a4a6b;",
    "}",
    ".feedback-comment .row {",
    "  display: flex; gap: 6px; justify-content: flex-end;",
    "}",
    ".feedback-comment button {",
    "  font-size: 12px; padding: 5px 10px; border-radius: 6px;",
    "  border: 1px solid #dde8f5; background: #fff; color: #5876a9;",
    "  cursor: pointer; font-family: inherit;",
    "}",
    ".feedback-comment button.primary {",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  border-color: transparent; color: #fff;",
    "}",
    ".footer {",
    "  padding: 6px 12px 8px; background: #fff;",
    "  border-top: 1px solid #eef2f9;",
    "  text-align: center;",
    "}",
    ".footer-text {",
    "  font-size: 11px; color: #8a9ab8; line-height: 1.4;",
    "}",
    ".footer-link {",
    "  background: transparent; border: none; cursor: pointer;",
    "  font-size: 11px; color: #8a9ab8; text-decoration: underline;",
    "  font-family: inherit; padding: 0;",
    "}",
    ".footer-link:hover { color: #5876a9; }",
    ".modal-overlay {",
    "  position: absolute; inset: 0;",
    "  background: rgba(58,74,107,0.35);",
    "  display: flex; align-items: center; justify-content: center;",
    "  padding: 16px; z-index: 10;",
    "}",
    ".modal-overlay[hidden] { display: none; }",
    ".modal {",
    "  background: #fff; border-radius: 12px; padding: 14px;",
    "  width: 100%; box-shadow: 0 8px 24px rgba(58,74,107,0.2);",
    "  display: flex; flex-direction: column; gap: 10px;",
    "}",
    ".modal h3 { margin: 0; font-size: 14px; color: #3a4a6b; font-weight: 700; }",
    ".modal p { margin: 0; font-size: 12px; color: #8a9ab8; }",
    ".modal textarea {",
    "  border: 1px solid #dde8f5; border-radius: 8px; padding: 8px;",
    "  resize: vertical; min-height: 80px; max-height: 180px;",
    "  font-family: 'Helvetica Neue', Arial, sans-serif;",
    "  font-size: 13px; color: #3a4a6b; outline: none;",
    "}",
    ".modal .row { display: flex; gap: 8px; justify-content: flex-end; }",
    ".modal button {",
    "  font-size: 13px; padding: 6px 12px; border-radius: 8px;",
    "  border: 1px solid #dde8f5; background: #fff; color: #5876a9;",
    "  cursor: pointer; font-family: inherit;",
    "}",
    ".modal button.primary {",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  border-color: transparent; color: #fff;",
    "}",
    ".figures {",
    "  margin-top: 10px; padding-top: 8px;",
    "  border-top: 1px dashed #dde8f5;",
    "  display: flex; flex-direction: column; gap: 8px;",
    "}",
    ".figures-label {",
    "  font-size: 9px; font-weight: 700; letter-spacing: 1.2px;",
    "  text-transform: uppercase; color: #8a9ab8;",
    "}",
    ".figure { display: flex; flex-direction: column; gap: 3px; }",
    ".figure a { display: block; line-height: 0; }",
    ".figure img {",
    "  display: block; width: 100%; height: auto;",
    "  max-height: 220px; object-fit: contain;",
    "  background: #f7f9fc;",
    "  border: 1px solid #dde8f5; border-radius: 6px;",
    "  cursor: zoom-in;",
    "}",
    ".figure-caption {",
    "  font-size: 11px; color: #8a9ab8; font-style: italic;",
    "  line-height: 1.35; word-break: break-word;",
    "}",
    ".previews { margin-top: 14px; display: grid; gap: 10px; }",
    ".preview-card {",
    "  display: flex; align-items: stretch; gap: 12px;",
    "  padding: 10px; border: 1px solid #dde8f5; border-radius: 8px;",
    "  background: #f7f9fc; text-decoration: none; color: #3a4a6b;",
    "  transition: border-color 120ms, background 120ms;",
    "}",
    ".preview-card:hover { border-color: #abc5ec; background: #fff; }",
    ".preview-card-image {",
    "  flex: 0 0 auto; width: 80px; height: 80px;",
    "  object-fit: cover; border-radius: 6px;",
    "  border: 1px solid #dde8f5; background: #fff;",
    "}",
    ".preview-card-favicon-wrap {",
    "  flex: 0 0 auto; width: 80px; height: 80px;",
    "  display: flex; align-items: center; justify-content: center;",
    "  border-radius: 6px; border: 1px solid #dde8f5; background: #fff;",
    "}",
    ".preview-card-favicon { width: 48px; height: 48px; object-fit: contain; }",
    ".preview-card-body {",
    "  min-width: 0; display: flex; flex-direction: column; justify-content: center;",
    "}",
    ".preview-card-site {",
    "  font-size: 10px; font-weight: 700; letter-spacing: 1.2px;",
    "  text-transform: uppercase; color: #7a8fb5;",
    "  margin-bottom: 2px;",
    "  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;",
    "}",
    ".preview-card-title {",
    "  font-size: 13px; font-weight: 600; color: #5876a9; line-height: 1.3;",
    "  display: -webkit-box; -webkit-line-clamp: 2;",
    "  -webkit-box-orient: vertical; overflow: hidden;",
    "}",
    ".preview-card-desc {",
    "  font-size: 12px; color: #7a8fb5; line-height: 1.4; margin-top: 3px;",
    "  display: -webkit-box; -webkit-line-clamp: 2;",
    "  -webkit-box-orient: vertical; overflow: hidden;",
    "}",
    ".site-preview {",
    "  margin-top: 10px; padding-top: 8px;",
    "  border-top: 1px dashed #dde8f5;",
    "  display: flex; flex-direction: column; gap: 8px;",
    "}",
    ".site-preview-label {",
    "  font-size: 9px; font-weight: 700; letter-spacing: 1.2px;",
    "  text-transform: uppercase; color: #8a9ab8;",
    "}",
    ".site-preview-block {",
    "  background: #f7f9fc; border: 1px solid #dde8f5;",
    "  border-radius: 8px; padding: 8px 10px; font-size: 12px;",
    "}",
    ".site-preview-block-title {",
    "  font-size: 9px; font-weight: 700; letter-spacing: 1.2px;",
    "  text-transform: uppercase; color: #8a9ab8; margin-bottom: 6px;",
    "}",
    ".site-preview-nav { display: flex; flex-wrap: wrap; gap: 4px; }",
    ".site-preview-nav-item {",
    "  background: #fff; border: 1px solid #dde8f5; border-radius: 5px;",
    "  padding: 3px 8px; font-size: 11px; color: #7a8fb5; font-weight: 500;",
    "}",
    ".site-preview-nav-item.active {",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  border-color: transparent; color: #fff; font-weight: 700;",
    "}",
    ".site-preview-path {",
    "  display: flex; flex-wrap: wrap; align-items: center; gap: 4px;",
    "}",
    ".site-preview-path-crumb {",
    "  background: #fff; border: 1px solid #dde8f5; border-radius: 5px;",
    "  padding: 2px 8px; font-size: 11px; color: #7a8fb5;",
    "}",
    ".site-preview-path-crumb.last { color: #5876a9; font-weight: 700; }",
    ".site-preview-path-sep { color: #b0bfd4; font-weight: 700; }",
    ".site-preview-steps { display: flex; flex-direction: column; gap: 5px; }",
    ".site-preview-step { display: flex; gap: 8px; align-items: flex-start; }",
    ".site-preview-step-num {",
    "  min-width: 18px; height: 18px; border-radius: 50%;",
    "  background: linear-gradient(135deg, #5876a9, #abc5ec);",
    "  color: #fff; font-size: 10px; font-weight: 700;",
    "  display: flex; align-items: center; justify-content: center; flex-shrink: 0;",
    "}",
    ".site-preview-step-text { font-size: 12px; color: #3a4a6b; line-height: 1.5; }",
    ".site-preview-link {",
    "  align-self: flex-start; font-size: 11px; color: #5876a9; text-decoration: underline;",
    "}",
    "@media (max-width: 600px) {",
    "  .btn { right: 16px; bottom: 16px; width: 52px; height: 52px; }",
    "  .panel {",
    "    position: fixed; inset: 0;",
    "    width: 100%; height: 100%;",
    "    border-radius: 0; border: none;",
    "    box-shadow: none;",
    "  }",
    "  .header { padding: 16px; padding-top: max(16px, env(safe-area-inset-top)); }",
    "  .messages { padding: 10px; }",
    "  .bubble { max-width: 95%; }",
    "  .input-row { padding: 8px 8px max(8px, env(safe-area-inset-bottom)); gap: 6px; }",
    "  .input-row textarea { font-size: 13px; padding: 8px 10px; }",
    "  .input-row .send { width: 34px; height: 34px; }",
    "  .footer { padding-bottom: max(8px, env(safe-area-inset-bottom)); }",
    "}"
  ].join("\n");

  var TEMPLATE = [
    '<button class="btn" type="button" aria-label="Open chat">',
    '  <svg class="icon-chat" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">',
    '    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>',
    '  </svg>',
    '  <svg class="icon-close" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" style="display:none;">',
    '    <line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/>',
    '  </svg>',
    '</button>',
    '<div class="panel" role="dialog" aria-label="Chat" hidden>',
    '  <div class="header">',
    '    <div class="avatar"></div>',
    '    <div class="title">',
    '      <div class="name"></div>',
    '      <div class="status" style="display:none;"></div>',
    '    </div>',
    '    <button class="close" type="button" aria-label="Close">',
    '      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">',
    '        <line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/>',
    '      </svg>',
    '    </button>',
    '  </div>',
    '  <div class="messages"></div>',
    '  <div class="input-row">',
    '    <textarea rows="1" placeholder=""></textarea>',
    '    <button class="send" type="button" aria-label="Send" disabled>',
    '      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">',
    '        <line x1="22" y1="2" x2="11" y2="13"/>',
    '        <polygon points="22 2 15 22 11 13 2 9 22 2"/>',
    '      </svg>',
    '    </button>',
    '  </div>',
    '  <div class="footer">',
    '    <span class="footer-text">Designed to improve automatically; <button type="button" class="footer-link general-feedback-btn">suggestions welcome</button>.</span>',
    '  </div>',
    '  <div class="modal-overlay" hidden>',
    '    <div class="modal" role="dialog" aria-label="Send feedback">',
    '      <h3>Share feedback</h3>',
    '      <p>Tell us what worked, what didn\'t, or anything you\'d like to see improved.</p>',
    '      <textarea class="modal-textarea" placeholder="Your feedback..."></textarea>',
    '      <div class="row">',
    '        <button type="button" class="modal-cancel">Cancel</button>',
    '        <button type="button" class="modal-send primary">Send</button>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
  ].join("\n");

  var SEND_ICON_SVG =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">' +
    '<line x1="22" y1="2" x2="11" y2="13"/>' +
    '<polygon points="22 2 15 22 11 13 2 9 22 2"/>' +
    '</svg>';

  var STOP_ICON_SVG =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">' +
    '<rect x="6" y="6" width="12" height="12" rx="2"/>' +
    '</svg>';

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function stripAttachTags(s) {
    return String(s).replace(/\[ATTACH:[^\]]*\]/g, "").replace(/\n{3,}/g, "\n\n").trim();
  }

  function renderInline(text) {
    var html = escapeHtml(text);
    // Convert markdown headings (# … ######) to bold text
    html = html.replace(/^(#{1,6})\s+(.+)$/gm, function (_, hashes, content) {
      return "<strong>" + content + "</strong>";
    });
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, t, u) {
      var safeUrl = /^(https?:|mailto:|\/)/i.test(u) ? u : "#";
      return '<a href="' + escapeHtml(safeUrl) + '" target="_blank" rel="noopener noreferrer">' + t + "</a>";
    });
    return html;
  }

  function hostOf(u) {
    try { return new URL(u).hostname; }
    catch (e) { return u; }
  }

  var SITE_NAV = [
    { name: "Bio & C.V.",     url: "/bio/" },
    { name: "Writings",       url: "/publication/" },
    { name: "Research Areas", url: "/#research-areas" },
    { name: "Software",       url: "/software/" },
    { name: "Dataverse",      url: "/dataverse/" },
    { name: "People",         url: "/research-group/" },
    { name: "Teaching",       url: "/teaching/" },
    { name: "GaryAI",         url: "/ask-gary/" },
    { name: "Contact",        url: "/contact/" }
  ];

  var SECTIONS = {
    bio:       { active: "Bio & C.V.",     path: ["Home", "Bio & C.V."],     url: "/bio/",            label: "Bio & C.V.",     steps: ["Click <strong>Bio &amp; C.V.</strong> in the top navigation", "Read the short biography and download the full CV"] },
    writings:  { active: "Writings",       path: ["Home", "Writings"],       url: "/publication/",    label: "Writings page",  steps: ["Click <strong>Writings</strong> in the top navigation", "Filter by type (articles, books, slides, briefs) or research area", "Click any title to open the abstract and PDF"] },
    research:  { active: "Research Areas", path: ["Home", "Research Areas"], url: "/#research-areas", label: "Research Areas", steps: ["Click <strong>Research Areas</strong> in the top navigation", "Browse the topical clusters (Causal Inference, Health Policy, &hellip;)", "Each card links to related papers and software"] },
    software:  { active: "Software",       path: ["Home", "Software"],       url: "/software/",       label: "Software index", steps: ["Click <strong>Software</strong> in the top navigation", "Pick a package (Amelia, MatchIt, Zelig, &hellip;)", "Each page has install commands, vignettes, and citations"] },
    dataverse: { active: "Dataverse",      path: ["Home", "Dataverse"],      url: "/dataverse/",      label: "Dataverse",      steps: ["Click <strong>Dataverse</strong> in the top navigation", "Find replication archives for published papers"] },
    people:    { active: "People",         path: ["Home", "People"],         url: "/research-group/", label: "Research group", steps: ["Click <strong>People</strong> in the top navigation", "Browse current group members, alumni, and collaborators"] },
    teaching:  { active: "Teaching",       path: ["Home", "Teaching"],       url: "/teaching/",       label: "Teaching page",  steps: ["Click <strong>Teaching</strong> in the top navigation", "See current courses, syllabi, and recordings where available"] },
    askgary:   { active: "GaryAI",         path: ["Home", "GaryAI"],         url: "/ask-gary/",       label: "GaryAI chat",    steps: ["Click <strong>GaryAI</strong> in the top navigation", "Type a question &mdash; that&rsquo;s this chatbot!"] },
    contact:   { active: "Contact",        path: ["Home", "Contact"],        url: "/contact/",        label: "Contact page",   steps: ["Click <strong>Contact</strong> in the top navigation", "Find email, office address, and assistant info"] }
  };

  var SITE_KEYWORD_MAP = [
    { keys: ["bio", "biography", "cv", "curriculum vitae", "resume", "about gary"], key: "bio" },
    { keys: ["writing", "paper", "publication", "article", "book", "preprint", "pdf", "slides", "presentation", "talk"], key: "writings" },
    { keys: ["research area", "research topic", "topic", "what does gary work on", "research interest"], key: "research" },
    { keys: ["software", "package", "amelia", "matchit", "zelig", "ei ", "ezi", "r package", "stata"], key: "software" },
    { keys: ["dataverse", "replication", "dataset", "data archive"], key: "dataverse" },
    { keys: ["people", "research group", "lab member", "student", "collaborator", "alumni", "postdoc"], key: "people" },
    { keys: ["teaching", "course", "syllabus", "class", "lecture"], key: "teaching" },
    { keys: ["ask gary", "garyai", "chatbot", "this bot", "the avatar", "this chat"], key: "askgary" },
    { keys: ["contact", "email", "reach", "office", "address"], key: "contact" }
  ];

  function findSitePreview(query) {
    var q = String(query || "").toLowerCase();
    if (!q) return null;
    for (var i = 0; i < SITE_KEYWORD_MAP.length; i++) {
      var entry = SITE_KEYWORD_MAP[i];
      for (var j = 0; j < entry.keys.length; j++) {
        if (q.indexOf(entry.keys[j]) !== -1) return SECTIONS[entry.key];
      }
    }
    return null;
  }

  function renderSitePreviewHtml(p) {
    if (!p) return "";
    var navHtml = SITE_NAV.map(function (item) {
      var cls = item.name === p.active ? "site-preview-nav-item active" : "site-preview-nav-item";
      return '<span class="' + cls + '">' + escapeHtml(item.name) + "</span>";
    }).join("");
    var pathHtml = p.path
      .map(function (c, i) {
        var cls = i === p.path.length - 1 ? "site-preview-path-crumb last" : "site-preview-path-crumb";
        var sep = i < p.path.length - 1 ? '<span class="site-preview-path-sep">&rsaquo;</span>' : "";
        return '<span class="' + cls + '">' + escapeHtml(c) + "</span>" + sep;
      })
      .join("");
    var stepsHtml = (p.steps || [])
      .map(function (s, i) {
        return (
          '<div class="site-preview-step">' +
          '<div class="site-preview-step-num">' + (i + 1) + "</div>" +
          '<div class="site-preview-step-text">' + s + "</div>" +
          "</div>"
        );
      })
      .join("");
    var link = p.url
      ? '<a class="site-preview-link" href="' + escapeHtml(p.url) + '" target="_blank" rel="noopener">Open ' + escapeHtml(p.label) + " &rarr;</a>"
      : "";
    return (
      '<div class="site-preview">' +
      '<div class="site-preview-label">Site preview &mdash; ' + escapeHtml(p.label) + "</div>" +
      '<div class="site-preview-block">' +
      '<div class="site-preview-block-title">Top navigation</div>' +
      '<div class="site-preview-nav">' + navHtml + "</div>" +
      "</div>" +
      '<div class="site-preview-block">' +
      '<div class="site-preview-block-title">Where to go</div>' +
      '<div class="site-preview-path">' + pathHtml + "</div>" +
      "</div>" +
      (stepsHtml
        ? '<div class="site-preview-block"><div class="site-preview-block-title">Steps</div><div class="site-preview-steps">' + stepsHtml + "</div></div>"
        : "") +
      link +
      "</div>"
    );
  }

  function renderPreviewsHtml(previews) {
    if (!previews || previews.length === 0) return "";
    var items = previews
      .map(function (p) {
        if (!p || !p.url) return "";
        var host = hostOf(p.url).replace(/^www\./, "");
        var siteName = p.site_name || host;
        var imgHtml;
        if (p.image) {
          imgHtml =
            '<img class="preview-card-image" src="' +
            escapeHtml(p.image) +
            '" alt="" loading="lazy" onerror="this.style.display=\'none\'">';
        } else {
          var favicon =
            "https://www.google.com/s2/favicons?domain=" +
            encodeURIComponent(host) +
            "&sz=128";
          imgHtml =
            '<div class="preview-card-favicon-wrap">' +
            '<img class="preview-card-favicon" src="' +
            escapeHtml(favicon) +
            '" alt="" loading="lazy" onerror="this.parentElement.style.display=\'none\'">' +
            "</div>";
        }
        var descHtml = p.description
          ? '<div class="preview-card-desc">' + escapeHtml(p.description) + "</div>"
          : "";
        return (
          '<a class="preview-card" href="' +
          escapeHtml(p.url) +
          '" target="_blank" rel="noopener noreferrer">' +
          imgHtml +
          '<div class="preview-card-body">' +
          '<div class="preview-card-site">' + escapeHtml(siteName) + "</div>" +
          '<div class="preview-card-title">' + escapeHtml(p.title || p.url) + "</div>" +
          descHtml +
          "</div>" +
          "</a>"
        );
      })
      .join("");
    return '<div class="previews">' + items + "</div>";
  }

  function renderFiguresHtml(figures) {
    if (!figures || figures.length === 0) return "";
    var items = figures
      .map(function (f) {
        if (!f || !f.url) return "";
        var url = escapeHtml(f.url);
        var alt = escapeHtml(f.caption || "");
        var captionParts = [];
        if (f.caption) captionParts.push(escapeHtml(f.caption));
        if (f.source_title) captionParts.push("— " + escapeHtml(f.source_title));
        var caption = captionParts.join(" ");
        return (
          '<div class="figure">' +
          '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' +
          '<img src="' + url + '" alt="' + alt + '" loading="lazy" />' +
          "</a>" +
          (caption ? '<div class="figure-caption">' + caption + "</div>" : "") +
          "</div>"
        );
      })
      .join("");
    return (
      '<div class="figures">' +
      '<div class="figures-label">Referenced figure' +
      (figures.length > 1 ? "s" : "") +
      "</div>" +
      items +
      "</div>"
    );
  }

  function init() {
    if (window.GKingChat && window.GKingChat.__mounted) return; // prevent double-mount

    var config = readConfig();
    if (!config.apiUrl) {
      console.error(
        "[GKing Chat Widget] apiUrl is required. Set window.GKingChatConfig.apiUrl or data-api-url on the script tag."
      );
      return;
    }

    var host = document.createElement("div");
    host.id = "gking-chat-widget";
    host.style.cssText = "all: initial;";
    document.body.appendChild(host);

    var shadow = host.attachShadow({ mode: "open" });
    var styleEl = document.createElement("style");
    styleEl.textContent = CSS;
    shadow.appendChild(styleEl);

    var wrapper = document.createElement("div");
    wrapper.innerHTML = TEMPLATE;
    while (wrapper.firstChild) shadow.appendChild(wrapper.firstChild);

    var btn = shadow.querySelector(".btn");
    var iconChat = shadow.querySelector(".icon-chat");
    var iconClose = shadow.querySelector(".icon-close");
    var panel = shadow.querySelector(".panel");
    var headerAvatar = shadow.querySelector(".header .avatar");
    var headerName = shadow.querySelector(".header .name");
    var closeBtn = shadow.querySelector(".close");
    var messagesEl = shadow.querySelector(".messages");
    var textarea = shadow.querySelector(".input-row textarea");
    var sendBtn = shadow.querySelector(".send");
    var generalFeedbackBtn = shadow.querySelector(".general-feedback-btn");
    var modalOverlay = shadow.querySelector(".modal-overlay");
    var modalTextarea = shadow.querySelector(".modal-textarea");
    var modalSendBtn = shadow.querySelector(".modal-send");
    var modalCancelBtn = shadow.querySelector(".modal-cancel");

    headerAvatar.textContent = config.avatarLabel;
    headerName.textContent = config.botName;
    textarea.placeholder = config.inputPlaceholder;

    var messages = [];
    var loading = false;
    var streaming = false;
    var abortController = null;
    var open = false;
    var conversationId = null;
    // Smooth streaming: tokens accumulate in streamTarget; an rAF loop copies
    // a growing prefix into messages[idx].content (3-8 chars/frame ≈ 200 cps),
    // so the UI animates smoothly instead of jumping per SSE delta.
    var streamTarget = "";
    var streamRevealed = 0;
    var streamRevealActive = false;
    var streamMsgIdx = -1;
    // Per-message feedback state, keyed by message.id:
    //   { rated: 'up'|'down'|null, commentOpen: bool, commentDraft: string, commentSent: bool }
    var feedbackState = {};

    function ensureConversationId() {
      if (!conversationId) conversationId = uuid();
      return conversationId;
    }

    function snapshotMessages() {
      return messages.map(function (m) {
        return { role: m.role, content: m.content };
      });
    }

    function postFeedback(payload) {
      var url = deriveFeedbackUrl(config);
      if (!url) {
        console.warn("[GKing Chat Widget] feedbackUrl not configured; payload not sent:", payload);
        return;
      }
      if (url === "console:") {
        console.log("[GKing Chat Widget] feedback (console mode):", payload);
        return;
      }
      try {
        fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          keepalive: true
        }).catch(function (e) {
          console.error("[GKing Chat Widget] feedback POST failed:", e);
        });
      } catch (e) {
        console.error("[GKing Chat Widget] feedback POST threw:", e);
      }
    }

    function buildFeedbackPayload(opts) {
      // opts: { messageId, ratedIndex, feedbackType, rating, comment }
      return {
        conversation_id: ensureConversationId(),
        message_id: opts.messageId,
        bot_id: config.botId,
        timestamp: new Date().toISOString(),
        feedback_type: opts.feedbackType,
        rating: opts.rating || null,
        comment: opts.comment || null,
        messages_snapshot: snapshotMessages(),
        rated_message_index: opts.ratedIndex == null ? null : opts.ratedIndex,
        page_url: location.href,
        user_agent: navigator.userAgent,
        widget_version: WIDGET_VERSION,
        source: "embed"
      };
    }

    function syncCommentDrafts() {
      // Preserve in-progress comment text across re-renders.
      var nodes = messagesEl.querySelectorAll("[data-comment-textarea]");
      for (var i = 0; i < nodes.length; i++) {
        var id = nodes[i].getAttribute("data-comment-textarea");
        if (feedbackState[id]) feedbackState[id].commentDraft = nodes[i].value;
      }
    }

    function renderFeedbackRow(m, msgIdx) {
      var st = feedbackState[m.id] || {};
      var rated = st.rated || null;
      var row = document.createElement("div");
      row.className = "feedback-row";
      row.innerHTML =
        '<button class="feedback-btn up' +
        (rated === "up" ? " active" : "") +
        '" type="button" aria-label="Helpful"' +
        (rated ? " disabled" : "") +
        ' data-action="rate-up" data-msg-id="' +
        escapeHtml(m.id) +
        '" data-msg-idx="' +
        msgIdx +
        '">' +
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="' +
        (rated === "up" ? "currentColor" : "none") +
        '" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 11v9a1 1 0 0 0 1 1h9.5a2 2 0 0 0 2-1.7l1.4-7A2 2 0 0 0 19 10h-5l1-4a2 2 0 0 0-2-2.5L8 11z"/><path d="M3 11h4v10H3z"/></svg>' +
        "</button>" +
        '<button class="feedback-btn down' +
        (rated === "down" ? " active" : "") +
        '" type="button" aria-label="Not helpful"' +
        (rated ? " disabled" : "") +
        ' data-action="rate-down" data-msg-id="' +
        escapeHtml(m.id) +
        '" data-msg-idx="' +
        msgIdx +
        '">' +
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="' +
        (rated === "down" ? "currentColor" : "none") +
        '" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 13V4a1 1 0 0 0-1-1H6.5a2 2 0 0 0-2 1.7l-1.4 7A2 2 0 0 0 5 14h5l-1 4a2 2 0 0 0 2 2.5L16 13z"/><path d="M21 13h-4V3h4z"/></svg>' +
        "</button>" +
        (st.commentSent ? '<span class="feedback-thanks">Thanks for your feedback.</span>' : "");
      return row;
    }

    function renderCommentBox(m, msgIdx) {
      var st = feedbackState[m.id] || {};
      var draft = st.commentDraft || "";
      var box = document.createElement("div");
      box.className = "feedback-comment";
      box.innerHTML =
        '<textarea data-comment-textarea="' +
        escapeHtml(m.id) +
        '" placeholder="What was wrong with this answer? (optional)"></textarea>' +
        '<div class="row">' +
        '<button type="button" data-action="comment-cancel" data-msg-id="' +
        escapeHtml(m.id) +
        '">No thanks</button>' +
        '<button type="button" class="primary" data-action="comment-send" data-msg-id="' +
        escapeHtml(m.id) +
        '" data-msg-idx="' +
        msgIdx +
        '">Send</button>' +
        "</div>";
      // textContent assignment preserves any characters the user typed
      var ta = box.querySelector("textarea");
      ta.value = draft;
      return box;
    }

    function renderMessages() {
      syncCommentDrafts();
      messagesEl.innerHTML = "";
      if (messages.length === 0) {
        var welcome = document.createElement("div");
        welcome.className = "msg bot";
        welcome.innerHTML =
          '<div class="avatar-sm">' +
          escapeHtml(config.avatarLabel) +
          '</div><div class="bubble">' +
          renderInline(config.welcomeMessage) +
          "</div>";
        messagesEl.appendChild(welcome);
      } else {
        messages.forEach(function (m, mi) {
          var node = document.createElement("div");
          node.className = "msg " + (m.role === "user" ? "user" : "bot");
          if (m.role === "user") {
            node.innerHTML = '<div class="bubble">' + escapeHtml(m.content) + "</div>";
          } else {
            var visible = stripAttachTags(m.content);
            var isLastForFigs = mi === messages.length - 1;
            var showExtras = !(streaming && isLastForFigs);
            var showFigures = m.figures && m.figures.length > 0 && showExtras;
            var showPreviews = m.previews && m.previews.length > 0 && showExtras;
            var showSitePreview = m.sitePreview && showExtras;
            node.innerHTML =
              '<div class="avatar-sm">' +
              escapeHtml(config.avatarLabel) +
              '</div><div class="bubble">' +
              renderInline(visible) +
              (showPreviews ? renderPreviewsHtml(m.previews) : "") +
              (showFigures ? renderFiguresHtml(m.figures) : "") +
              (showSitePreview ? renderSitePreviewHtml(m.sitePreview) : "") +
              "</div>";
          }
          messagesEl.appendChild(node);
          var isLast = mi === messages.length - 1;
          var canRate =
            m.role === "assistant" &&
            !!stripAttachTags(m.content) &&
            !(streaming && isLast);
          if (canRate) {
            messagesEl.appendChild(renderFeedbackRow(m, mi));
            var st = feedbackState[m.id];
            if (st && st.commentOpen) {
              messagesEl.appendChild(renderCommentBox(m, mi));
            }
          }
        });
      }
      if (
        loading &&
        (messages.length === 0 || messages[messages.length - 1].role !== "assistant")
      ) {
        var typing = document.createElement("div");
        typing.className = "msg bot";
        typing.innerHTML =
          '<div class="avatar-sm">' +
          escapeHtml(config.avatarLabel) +
          '</div><div class="typing"><span></span><span></span><span></span></div>';
        messagesEl.appendChild(typing);
      }
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function setOpen(next) {
      open = next;
      panel.hidden = !open;
      btn.setAttribute("aria-label", open ? "Close chat" : "Open chat");
      iconChat.style.display = open ? "none" : "";
      iconClose.style.display = open ? "" : "none";
      if (open) {
        renderMessages();
        setTimeout(function () {
          textarea.focus();
        }, 0);
      }
    }

    function isBusy() { return loading || streaming; }

    function updateSendState() {
      if (isBusy()) {
        sendBtn.disabled = false;
        sendBtn.innerHTML = STOP_ICON_SVG;
        sendBtn.setAttribute("aria-label", "Stop");
        sendBtn.classList.add("stop");
      } else {
        sendBtn.disabled = !textarea.value.trim();
        sendBtn.innerHTML = SEND_ICON_SVG;
        sendBtn.setAttribute("aria-label", "Send");
        sendBtn.classList.remove("stop");
      }
    }

    function handleSendClick() {
      if (isBusy()) {
        if (abortController) {
          try { abortController.abort(); } catch (e) {}
        }
      } else {
        send();
      }
    }

    function setLoading(v) {
      loading = v;
      updateSendState();
      renderMessages();
    }

    function startRevealLoop() {
      if (streamRevealActive) return;
      streamRevealActive = true;
      function tick() {
        if (!streamRevealActive) return;
        if (streamRevealed < streamTarget.length && streamMsgIdx >= 0 && messages[streamMsgIdx]) {
          var remaining = streamTarget.length - streamRevealed;
          var step = Math.max(3, Math.min(8, Math.ceil(remaining * 0.08)));
          streamRevealed = Math.min(streamRevealed + step, streamTarget.length);
          messages[streamMsgIdx].content = streamTarget.slice(0, streamRevealed);
          renderMessages();
        }
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    }

    function stopRevealLoop() {
      streamRevealActive = false;
      if (streamMsgIdx >= 0 && messages[streamMsgIdx] && streamTarget) {
        messages[streamMsgIdx].content = streamTarget;
        renderMessages();
      }
      streamTarget = "";
      streamRevealed = 0;
      streamMsgIdx = -1;
    }

    async function send() {
      var text = textarea.value.trim();
      if (!text || loading) return;
      textarea.value = "";
      ensureConversationId();
      var pendingSitePreview = findSitePreview(text);
      messages.push({ id: uuid(), role: "user", content: text });
      setLoading(true);

      abortController = new AbortController();
      try {
        var res = await fetch(config.apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            botId: config.botId,
            messages: messages,
            conversation_id: ensureConversationId(),
            source: "embed"
          }),
          signal: abortController.signal
        });

        var ct = res.headers.get("Content-Type") || "";
        if (ct.indexOf("text/event-stream") !== -1 && res.body && res.body.getReader) {
          var reader = res.body.getReader();
          var decoder = new TextDecoder();
          var buffer = "";
          messages.push({ id: uuid(), role: "assistant", content: "", sitePreview: pendingSitePreview });
          var idx = messages.length - 1;
          streaming = true;
          setLoading(false);

          // Hand the assistant slot to the rAF reveal loop.
          streamTarget = "";
          streamRevealed = 0;
          streamMsgIdx = idx;
          startRevealLoop();

          while (true) {
            var chunk = await reader.read();
            if (chunk.done) break;
            buffer += decoder.decode(chunk.value, { stream: true });
            var lines = buffer.split("\n");
            buffer = lines.pop() || "";
            for (var i = 0; i < lines.length; i++) {
              var line = lines[i];
              if (line.indexOf("data: ") !== 0) continue;
              try {
                var evt = JSON.parse(line.slice(6));
                if (evt.type === "token" && evt.content) {
                  streamTarget += evt.content;
                } else if (evt.type === "attached_figures") {
                  messages[idx].figures = Array.isArray(evt.figures) ? evt.figures : [];
                } else if (evt.type === "previews") {
                  messages[idx].previews = Array.isArray(evt.items) ? evt.items : [];
                } else if (evt.type === "meta") {
                  messages[idx].meta = evt;
                }
              } catch (e) {
                // skip malformed events
              }
            }
          }

          stopRevealLoop();
          if (!messages[idx].content) {
            messages[idx].content = "Sorry, I couldn't generate a response.";
          }
          streaming = false;
          updateSendState();
          renderMessages();
        } else {
          var data;
          try {
            data = await res.json();
          } catch (e) {
            data = null;
          }
          var reply =
            (data && (data.reply || data.message || data.response)) ||
            "Sorry, I couldn't generate a response.";
          var figs = data && Array.isArray(data.figures) ? data.figures : [];
          var previews = data && Array.isArray(data.previews) ? data.previews : [];
          messages.push({ id: uuid(), role: "assistant", content: reply, figures: figs, previews: previews, sitePreview: pendingSitePreview });
          setLoading(false);
        }
      } catch (e) {
        var wasAbort =
          e && (e.name === "AbortError" || /aborted/i.test(String(e.message || "")));
        stopRevealLoop();
        streaming = false;
        if (wasAbort) {
          var last = messages[messages.length - 1];
          if (last && last.role === "assistant" && !last.content) {
            last.content = "_(stopped)_";
          }
        } else {
          console.error("[GKing Chat Widget] request error:", e);
          messages.push({
            id: uuid(),
            role: "assistant",
            content: "Sorry, something went wrong. Please try again."
          });
        }
        setLoading(false);
      } finally {
        abortController = null;
      }
    }

    btn.addEventListener("click", function () {
      setOpen(!open);
    });
    closeBtn.addEventListener("click", function () {
      setOpen(false);
    });
    sendBtn.addEventListener("click", handleSendClick);
    textarea.addEventListener("input", updateSendState);
    textarea.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendClick();
      }
    });

    messagesEl.addEventListener("click", function (e) {
      var target = e.target;
      while (target && target !== messagesEl && !target.getAttribute("data-action")) {
        target = target.parentNode;
      }
      if (!target || target === messagesEl) return;
      var action = target.getAttribute("data-action");
      var msgId = target.getAttribute("data-msg-id");
      var msgIdxAttr = target.getAttribute("data-msg-idx");
      var msgIdx = msgIdxAttr == null ? null : parseInt(msgIdxAttr, 10);
      if (!msgId) return;

      if (action === "rate-up" || action === "rate-down") {
        if (feedbackState[msgId] && feedbackState[msgId].rated) return;
        var rating = action === "rate-up" ? "up" : "down";
        feedbackState[msgId] = {
          rated: rating,
          commentOpen: rating === "down",
          commentDraft: "",
          commentSent: false
        };
        postFeedback(
          buildFeedbackPayload({
            messageId: msgId,
            ratedIndex: msgIdx,
            feedbackType: "rating",
            rating: rating
          })
        );
        renderMessages();
      } else if (action === "comment-cancel") {
        if (feedbackState[msgId]) {
          feedbackState[msgId].commentOpen = false;
          feedbackState[msgId].commentDraft = "";
        }
        renderMessages();
      } else if (action === "comment-send") {
        var ta = messagesEl.querySelector('[data-comment-textarea="' + msgId + '"]');
        var commentText = ta ? ta.value.trim() : "";
        if (!feedbackState[msgId]) feedbackState[msgId] = {};
        feedbackState[msgId].commentOpen = false;
        feedbackState[msgId].commentDraft = "";
        feedbackState[msgId].commentSent = true;
        if (commentText) {
          postFeedback(
            buildFeedbackPayload({
              messageId: msgId,
              ratedIndex: msgIdx,
              feedbackType: "comment",
              rating: feedbackState[msgId].rated || null,
              comment: commentText
            })
          );
        }
        renderMessages();
      }
    });

    function openFeedbackModal() {
      modalTextarea.value = "";
      modalOverlay.hidden = false;
      setTimeout(function () {
        modalTextarea.focus();
      }, 0);
    }
    function closeFeedbackModal() {
      modalOverlay.hidden = true;
    }
    generalFeedbackBtn.addEventListener("click", openFeedbackModal);
    modalCancelBtn.addEventListener("click", closeFeedbackModal);
    modalSendBtn.addEventListener("click", function () {
      var text = modalTextarea.value.trim();
      if (!text) {
        closeFeedbackModal();
        return;
      }
      postFeedback(
        buildFeedbackPayload({
          messageId: "general",
          ratedIndex: null,
          feedbackType: "general",
          rating: null,
          comment: text
        })
      );
      closeFeedbackModal();
    });
    modalOverlay.addEventListener("click", function (e) {
      if (e.target === modalOverlay) closeFeedbackModal();
    });

    window.GKingChat = {
      __mounted: true,
      open: function () {
        setOpen(true);
      },
      close: function () {
        setOpen(false);
      },
      toggle: function () {
        setOpen(!open);
      },
      reset: function () {
        messages = [];
        feedbackState = {};
        conversationId = null;
        renderMessages();
      },
      config: config
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
