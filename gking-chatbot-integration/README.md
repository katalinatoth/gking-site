# Gary King AI Avatar — website integration

You are integrating Professor Gary King's AI chatbot into his existing website.
Two surfaces are needed:

1. **A site-wide popup widget** — a floating chat launcher that appears on
   every page in the bottom-right corner.
2. **A dedicated chatbot page** — a full-page chat experience at a route the
   team picks (e.g. `/ai`, `/chat`, `/ask-gary`).

Both surfaces talk to a backend that's already deployed on AWS (S3-hosted
chat UI + a streaming Lambda Function URL for chat, plus a buffered
Lambda behind API Gateway for feedback). You do **not** need to deploy
any backend, manage any keys, or stand up any infrastructure. Everything
below is paste-and-go.

The chat endpoint streams responses as Server-Sent Events
(`Content-Type: text/event-stream`), one `data: {...}` event per token
batch — both surfaces in this package already handle that. Feedback is a
plain JSON `POST` returning `{"ok": true}`.

---

## What's in this package

```
gking-chatbot-integration/
├── README.md                       ← you are here
├── snippets/
│   ├── widget-script-tag.html      ← paste in site-wide template (popup)
│   └── chatbot-page-iframe.html    ← paste on the dedicated page
└── widget/
    ├── gking-chat-widget.js        ← the widget source (already hosted; included for reference / self-host)
    └── demo.html                   ← standalone test page (must be served over HTTP — see below)
```

---

## Live endpoints (already deployed, do not change)

| Resource | URL |
|---|---|
| Widget JS (CDN-style, served from S3) | `https://gking-avatar-deploy-750630108795.s3.us-east-2.amazonaws.com/widget/gking-chat-widget.js` |
| Dedicated chat page | `https://gking-avatar-deploy-750630108795.s3.us-east-2.amazonaws.com/chat/index.html` |
| Chat API (streaming SSE) | `https://y455vtbsy5pinfj5c2s3xmxqo40nwkno.lambda-url.us-east-2.on.aws/` |
| Feedback API (JSON) | `https://sn74dkx04g.execute-api.us-east-2.amazonaws.com/feedback` |

CORS is open (`Access-Control-Allow-Origin: *`) so these endpoints can be
loaded/called from any origin, including Gary's domain.

> **Local-testing gotcha.** Don't open `widget/demo.html` via `file://`.
> Browsers send `Origin: null` for `file://` pages, and the buffered
> feedback API (still on API Gateway HTTP API) strips its CORS headers
> in that case, so feedback POSTs will fail preflight. The chat
> Function URL is more permissive but still safer to test over HTTP:
>
> ```
> cd widget && python3 -m http.server 8000
> # open http://localhost:8000/demo.html
> ```
>
> On Gary's actual HTTPS site this is a non-issue — the browser sends a
> real `https://...` Origin header and CORS works on both endpoints.

---

## Task 1 — popup widget on every page

**What:** Embed a single `<script>` tag in the site's shared layout/template
so every page renders a floating chat button.

**File to copy from:** `snippets/widget-script-tag.html`

**Where to paste:** The closing `</body>` of the site-wide layout. If the
site is built with a static-site generator / template engine, find the
"footer" or "layout" partial that wraps every page. If it's WordPress, the
right place is `footer.php` or via a "Custom HTML before </body>" plugin.

**Verification steps after deploy:**

1. Visit any page on Gary's site.
2. A circular blue button should appear in the bottom-right corner.
3. Click it → a chat panel opens, header reads **"Gary King's AI Avatar"**.
4. Send a test message ("hi") → expect characters to appear progressively
   within ~2–15s (longer on the first request after a quiet period —
   Lambda cold start). If the whole reply pops in at once, you're probably
   on a stale cached widget JS — see the streaming row in Troubleshooting.
5. Click the thumbs-up icon under the response → no visible change is
   required, but check the browser DevTools Network tab; you should see a
   `POST` to `…/feedback` returning `200` with `{"ok": true, "id": "..."}`.
6. Click "Send feedback about this bot" at the bottom of the panel, type a
   note, click Send → another `200` from `…/feedback`.

**Customization (optional):** any of the `data-*` attributes on the script
tag can be changed without editing the JS. Common edits:

- `data-welcome-message` — the greeting shown before the user types.
- `data-input-placeholder` — placeholder text in the text box.
- `data-bot-name` / `data-avatar-label` — header title and avatar initials.

Do **not** change `data-api-url`, `data-feedback-url`, or `data-bot-id`
unless you also coordinate a backend change.

**Constraints:**
- The host page **must** be served over HTTPS. Browsers will block the
  widget's API calls from an HTTP page.
- The widget uses Shadow DOM, so the host site's CSS cannot leak into it
  and vice versa. No CSS reset / scoping work needed.
- The widget is ~33 KB ungzipped (~9 KB gzipped). Loaded with `defer`, so
  it does not block initial render.

---

## Task 2 — dedicated chatbot page

**What:** Create a new page on Gary's site (e.g. at route `/ai` or
`/chat`) whose body is a full-viewport iframe pointing at the hosted chat
UI.

**File to copy from:** `snippets/chatbot-page-iframe.html`

**Where to paste:** Inside the `<body>` of a new page in the site. Strip
or minimize any surrounding chrome (top nav can stay, but reserve the rest
for the iframe). The recommended approach is a near-empty page wrapper
with the iframe at full height.

**Verification steps after deploy:**

1. Navigate to the new route on Gary's site.
2. The iframe should load a full-viewport chat interface with the title
   "Gary King — AI Avatar".
3. Send a test message → expect a streamed reply with the same latency
   profile as the widget.
4. Try a query that retrieves a figure (e.g. "show me a chart from your
   media censorship paper") — referenced figures should render as images
   below the response.
5. Per-message thumbs up/down and the "Send feedback about this bot"
   button at the bottom should both POST to the feedback API (verify in
   DevTools).

**Why an iframe (and not a self-hosted React build)?**
- The chat UI is already built and hosted; no rebuild needed when content
  or model changes — just refresh.
- Site CSS cannot break the chat UI and vice versa.
- Updates roll out without redeploying Gary's site.

**If the team strongly prefers a self-hosted build** instead of an
iframe, contact the backend owner — the React source is in a separate
repo (`gking-avatar-v2`) and can be re-exported with a different
`basePath` for the team's chosen route. But iframe is the recommended
default and what's currently set up.

**Constraints:**
- iframe must be on an HTTPS page (same reason as Task 1).
- Set the iframe height appropriately. `100vh` works on a chrome-less
  page; if the site has a sticky header of height `H`, use
  `style="height:calc(100vh - Hpx)"`.

---

## Logging and privacy

Every chat turn and every feedback event is logged on the backend (S3,
private bucket). Logs include:

- Conversation turn: timestamp, conversation ID, both messages, model
  name, latency, **salted SHA-256 hash of the user's IP** (not raw IP),
  user-agent string.
- Feedback event: same payload the widget sends (rating up/down,
  optional comment, message snapshot, page URL, user-agent), plus the
  same hashed IP.

The backend already implements this; you do not need to add any
client-side logging. Do not add additional analytics/tracking that
forwards user messages to third parties without checking with Gary
first.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Widget button not visible | Script blocked by Content-Security-Policy | Add `https://gking-avatar-deploy-750630108795.s3.us-east-2.amazonaws.com` to `script-src`, and add `https://y455vtbsy5pinfj5c2s3xmxqo40nwkno.lambda-url.us-east-2.on.aws` (chat) + `https://sn74dkx04g.execute-api.us-east-2.amazonaws.com` (feedback) to `connect-src` |
| Widget visible but `apiUrl is required` console error | A `data-api-url` typo or missing | Re-copy the snippet verbatim |
| Chat returns "Sorry, something went wrong" on every message — DevTools shows CORS error and `Origin: null` | Page served via `file://` | Serve over HTTP/HTTPS instead — see the local-testing note above |
| Chat returns "Sorry, something went wrong" on every message | API blocked by network rules | Open DevTools → Network → look at the `POST` to the chat URL. If status is 0 or CORS error, a firewall is blocking outbound HTTPS to AWS Lambda (`*.lambda-url.us-east-2.on.aws`) |
| Chat reply shows up all at once instead of streaming | Either the page is loading the Function URL through a proxy/CDN that buffers responses, or the surface is consuming the JSON fallback path (e.g. an old widget JS) | Verify `Content-Type: text/event-stream` on the `POST` chat response. If you see `application/json`, your widget JS is stale — re-fetch from S3 |
| First message takes ~15s, subsequent are fast | Lambda cold start (expected) | Not a bug. If unacceptable, ask backend owner to enable a keep-warm ping |
| Feedback button does nothing visible | Designed that way | Verify in DevTools that `POST /feedback` returned `200` |

---

## Out of scope for the web team

You do **not** need to:
- Manage AWS credentials or keys
- Deploy any backend
- Bundle, transpile, or build the widget — it's a single drop-in script
- Set up CORS on Gary's site — the API allows all origins
- Handle user authentication — the bot is public/anonymous
- Store or process chat logs — the backend does it

If you find yourself doing any of the above, stop and confirm with the
backend owner that you're not duplicating work.
