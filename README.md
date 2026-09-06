# Quiz Platform

A full-stack educational quiz platform built with Django, Django REST Framework,
and vanilla JavaScript.

## Features

- **Auth**: register, log in, log out. Authenticated users and anonymous guests
  can both take quizzes.
- **Quiz taking**: browse categories → quizzes → take one question at a time.
  Every selection is saved immediately via API. Submitting with unanswered
  questions is blocked with per-question indicators. Authenticated users may
  take a quiz **up to 3 times** (guests get one locked attempt); each attempt
  is graded, stored, and locked in on submission.
- **Attempt review & history**: "My Scores" lists every attempt (1st/2nd/3rd)
  with a **Review** page per attempt showing the question, your answer, the
  correct answer (green/red), and points earned. Snapshots of question/answer
  text keep old attempts accurate even if the quiz is edited later. The take
  page shows your latest score and offers a fresh attempt while attempts remain.
- **Private quizzes**: gated by an access code; the code unlocks the quiz for
  the session.
- **Quiz creation** (authenticated): dynamic add/remove of questions (max 50)
  and answers (min 2, at least one correct). Points are validated and the
  quiz total always equals the sum of its questions' points.
- **Math questions**: per-question "Math" toggle. The rendering engine follows the active
  site language — **Arabic** authoring and rendering uses **Khatt** (`khatt.org/api`),
  Arabic mathematical notation rendered as images; **English** uses LaTeX via KaTeX.
  In Arabic, the builder ships a clickable **symbol palette** with the most popular
  structures and symbols (fraction, root, power, summation, integral, limit, bracket,
  matrix, ±, ×, ÷, ∩, ∪, π, ∞, inequalities, ∈, ∅, ∃, →, ←) where
  every symbol is a live Khatt-rendered image; clicking one opens a small editor to fill
  in its parts, live-previews the result, and inserts the image at the cursor with its
  natural width/height. The palette thumbnails are **loaded lazily** — nothing is fetched
  from khatt.org until the teacher opens a question's "Symbols & templates" toggler — and
  insertions reuse the editor's already-loaded preview image, so each insert costs no
  extra API request. In English, the LaTeX guide + KaTeX live preview is unchanged.
  Images are embedded directly in the question/answer text and sanitized on output
  (only `khatt.org` `<img>` tags pass).
- **My Scores**: every attempt with its score, attempt number, and a link to
  review the answers.
- **AI feedback**: "Ask AI" on the **attempt review page** returns an Ollama
  Cloud-generated explanation (based on that attempt's chosen answer) rendered
  as sanitized HTML (markdown + bleach).
- **Offline quiz download** (authenticated): a registered user can download **any
  quiz** as a single self-contained HTML file that runs entirely offline — no
  internet, no CDN, no server. It reproduces the live take experience: the same
  design, one-question-at-a-time navigation, the same countdown timer, and an
  after-finish review (your answer vs. the correct one, points earned) scored
  locally from data embedded in the file. Everything is bundled: KaTeX (JS/CSS/woff2
  fonts) when the quiz has LaTeX math, khatt formula images and uploaded question
  images as `data:` URIs, plus inline CSS/JS. Answers are kept in the browser's
  `localStorage` (resumed across reloads / survives refreshes) and are never sent
  to the server. Accessible from the take page's sidebar, the submitted card, the
  "My Scores" table, and the answer-review page. Works in the active site language
  (en/ar, with correct `dir`).
- **Admin**: all core models registered with sensible list displays.

## Tech stack

| Component | Version |
|---|---|
| Python | 3.10 |
| Django | 5.2.17 (LTS) |
| Django REST Framework | 3.18.0 |
| django-environ | 0.14.0 |
| Database | SQLite (default) / PostgreSQL via `DATABASE_URL` |
| Testing | pytest 9.1, pytest-django 4.14, factory_boy 3.3.3 |
| LLM | Ollama Cloud (`https://ollama.com`, OpenAI-compatible API via httpx 0.28.1) |
| Frontend | Bootstrap 5.3.8, Font Awesome 7.3.1, KaTeX 0.16.11 (CDN), Khatt math images, vanilla JS |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env          # then set SECRET_KEY and OLLAMA_API_KEY
python manage.py migrate
python manage.py seed_demo    # sample categories + quizzes (private quiz code: SPACE42)
python manage.py runserver
```

### AI feedback (Ollama Cloud)

"Ask AI" calls Ollama's hosted API. Create an API key at
https://ollama.com/settings/keys and set it in `.env`:

```bash
OLLAMA_API_KEY=your-key-here
```

Defaults target Ollama Cloud (`OLLAMA_HOST=https://ollama.com`,
`OLLAMA_MODEL=gpt-oss:120b`). To use a local Ollama server instead, set
`OLLAMA_HOST=http://localhost:11434` and a locally-pulled model name (no key
needed). If `OLLAMA_API_KEY` is missing while talking to `ollama.com`, "Ask AI"
returns 503 with a clear message.

Open http://127.0.0.1:8000/

### Creating LaTeX questions

In **New Quiz**, tick **Math** on a question.

**English mode (LaTeX / KaTeX):** the builder reveals the LaTeX guide and a live
preview. Type formulas inline between `$...$` (e.g. `$E = mc^2$`) or `\(...\)`,
display formulas between `$$...$$` or `\[...\]`, and paste ready-made snippets from
the guide (fraction, power, vector, integral, matrix, Greek letters, etc.). The
preview renders as you type, and malformed formulas are flagged before you save.

Basic notation quick reference:

| You type | Result |
|---|---|
| `$x^2$` | x² |
| `$\frac{a}{b}$` | a/b as a fraction |
| `$\sqrt{x}$` / `$\sqrt[n]{x}$` | √x / nth root |
| `$x_i$` | x with subscript i |
| `$\vec{F}$` | vector F |
| `$\int_{a}^{b} f(x)\,dx$` | integral |
| `$\sum_{i=1}^{n} i$` | summation |
| `$f(x) = x^2 + 1$`, `$x \mapsto f(x)$` | functions |
| `$\sin(x)$`, `$\cos(x)$`, `$\tan(x)$` | trig |
| `$\ln(x)$`, `$\log_{b}(x)$`, `$e^{x}$` | logs / exponential |
| `$\pi$`, `$\alpha$`, `$\theta$` | Greek letters |
| `$\pm$`, `$\infty$`, `$\approx$`, `$\leq$`, `$\geq$` | symbols |
| `$\lvert x \rvert$`, `$\lfloor x \rfloor$`, `$\lceil x \rceil$` | absolute value, floor, ceiling |
| `$\textbf{word}$` | **bold** text (e.g. emphasize "EXCEPT for") |
| `$\textcolor{red}{\textbf{word}}$` | red text (`blue` / `green` also work) |
| `$\begin{pmatrix} a & b \\ c & d \end{pmatrix}$` | matrix |

Every copyable template pastes with **`[type in here]`** markers showing exactly
where to type your expression (e.g. copying *Fraction* gives
`$\frac{[type in here]}{[type in here]}$`). The guide cards themselves show the
plain example (`$\frac{a}{b}$`). Pasting a template **inside** an existing math
region automatically strips the redundant `$…$` delimiters, so nesting works:
select a `[type in here]` marker, paste *Sine* into `$f(x) = [type in here]$`,
and you get `$f(x) = \sin([type in here])$`.

Wrap text in `$...$`; `\frac{a}{b}`, `^`, `_`, `\sqrt`, `\vec`, `\int`, `\sum`
and the Greek/symbol commands above cover most physics and math notation.

### Creating Arabic math questions (Khatt)

When the site is in **Arabic**, ticking **Math** on a question switches the builder
to a **symbol palette** instead of the LaTeX guide. Every palette item shows the
symbol itself as a live image rendered by Khatt (`https://khatt.org/api?c=...`):
fractions (`/على{بسط}{مقام}`), square/nth roots (`/جذر{...}`), powers (`^{...}`),
summations (`/مج{...}{...}`), limits (`/نها{...}{...}`), integrals (`/تكا{...}{...}`),
brackets (`/قوس{...}`), matrices (`/مصفوفة`), plus a curated set of the most
popular operators and relations (+ `+`, − `-`, ± `/زائد.ناقص`, × `/ضرب`, ÷ `/قسمة`,
∩ `/تقاطع`, ∪ `/اتحاد`, π, ∞, ≤, ≥, ≠, ≈, ∈, ∅, ∃, →, ←, and a space symbol
`/مسافة`) — a deliberately trimmed catalog so only commonly used symbols are shown.
Numbers render in Arabic numerals (Khatt's default); command names/templates
match the official `documentation` at khatt.org.

Click a structure symbol → a small dialog opens with a field for each part
(e.g. numerator/denominator). Fill them in; the dialog shows a live image preview,
then **Insert** renders the final formula as a Khatt image and places it in the
question/answer box at the cursor, with its natural width and height (reusing the
preview image's dimensions when available, so insertion needs no extra request).
Clicking a plain symbol (like `±`) inserts it immediately. The palette thumbnails
are loaded lazily on first open to minimize khatt.org API calls. The stored text
contains the embedded `<img>` tags; they render on the take and review pages, and
output is sanitized so only `khatt.org` images pass.

The full Khatt command language is documented at https://khatt.org/documentation.

## Configuration

All secrets come from environment variables (`.env` via django-environ):

- `SECRET_KEY` — Django secret key (required in production)
- `DEBUG` — `True`/`False`
- `ALLOWED_HOSTS` — comma-separated
- `DATABASE_URL` — e.g. `postgres://user:pass@localhost:5432/quiz` or `sqlite:///db.sqlite3`
- `OLLAMA_HOST` — Ollama base URL, default `https://ollama.com` (Cloud); use
  `http://localhost:11434` for a local server
- `OLLAMA_MODEL` — model to use, default `gpt-oss:120b`
- `OLLAMA_API_KEY` — Ollama Cloud API key (from https://ollama.com/settings/keys),
  sent as `Authorization: Bearer`; required when `OLLAMA_HOST` is `ollama.com`
- `LOG_LEVEL` / `LOG_FILE` — logging

## Tests

```bash
pytest
```

247 tests covering the service layer (scoring, attempts, point totals, guest
sessions, AI prompt building incl. Khatt `<img>` stripping, quiz validation,
offline export incl. khatt/KaTeX/image inlining and view gating), the
sanitizer filter (`|rich`), and the key API/UI endpoints (save-answer,
submit, access codes, attempt limits, review pages, auth, My Scores, Arabic
Khatt rendering vs. English KaTeX rendering).

## Architecture

Five feature apps plus one minimal shared app; views are thin, business logic
lives in service layers.

```
config/           settings, URL routing, WSGI/ASGI
core/             shared: session store (guests + access codes), non-blocking logging, seed_demo
accounts/         register/login/logout
catalog/          Category + browse views
quizzes/          Quiz/Question/Answer models, take + create UI, content services/selectors
scoring/          Score + SelectedAnswer models, save/submit services, My Scores, DRF API
ai_feedback/      Ollama Cloud prompt building + sanitized markdown rendering, DRF API
```

Key design decisions:

- **Point totals are computed** from `SUM(question.points)` on read — no
  denormalized counter to go stale.
- **Lock-in** for authenticated users is enforced by a DB unique constraint on
  `Score (user, quiz)`; guests lock via a session flag. Both checked by the
  service before any mutation.
- **Guest state** lives behind `core.sessions.QuizSessionStore`; views never
  touch `request.session` directly.
- **Services = writes, selectors = reads.** `views.py`/`api.py` only parse
  input, call a service, and return a response.
- **AI HTML is sanitized** with `bleach` after `markdown` rendering.

## API endpoints

| Method | URL | Purpose |
|---|---|---|
| POST | `/api/quizzes/<id>/answers/` | Save an answer immediately (guest or auth) |
| POST | `/api/quizzes/<id>/submit/` | Compute + lock in the score |
| POST | `/api/questions/<id>/ai-explain/` | Ollama Cloud explanation (returns HTML) |
