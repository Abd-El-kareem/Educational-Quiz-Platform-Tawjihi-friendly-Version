# PROJECT_MAP

## [TECH_STACK]
- Python 3.10 · Django 5.2.17 LTS · DRF 3.18.0 · django-environ 0.14.0
- DB: SQLite (default) / PostgreSQL via `DATABASE_URL` (psycopg 3.3.4)
- pytest 9.1.1 · pytest-django 4.14.0 · factory_boy 3.3.3
- LLM: Ollama Cloud via OpenAI-compatible `https://ollama.com/v1/chat/completions`
  (httpx 0.28.1, `Authorization: Bearer <OLLAMA_API_KEY>`)
- markdown 3.10.3 · bleach 6.4.0 · Pillow 12.3.0
- Bootstrap 5.3.8 · Font Awesome 7.3.1 (jsdelivr CDN) · Vanilla JS (fetch)
- LaTeX: KaTeX 0.16.11 (jsdelivr CDN) + auto-render, client-side only;
  per-question opt-in via `Question.math_enabled` (renders question text AND
  answers). Builder ships a copy-paste template guide + live preview
  (`static/js/latex_helper.js`)
- Arabic math (Khatt): when the active language is Arabic, math questions are
  authored/rendered with Khatt (`https://khatt.org/api?c=<encoded command>`,
  no key, PNG, 7-day public CDN cache, public-domain). Builder shows a clickable
  symbol palette (`static/js/khatt_helper.js`) trimmed to the most popular,
  verified commands (9 structures + 19 literals incl. +, −, and `/مسافة`); each
  symbol is a live Khatt image. Numbers render in Arabic (Eastern) numerals,
  Khatt's default. Thumbnails are lazy — no `src` until `KHATT_HELPER.reveal()` on first
  toggle-cheatsheet click (`static/js/quiz_builder.js`), so no API call fires
  until the teacher opens the palette. Structure clicks open a modal with
  per-part inputs + live preview; Insert reuses the preview image's
  `naturalWidth/Height` when the command matches (no extra request) and places
  `<img src="khatt.org..." width height>` at the cursor. Display/output
  sanitized by `quizzes/templatetags/quiz_filters.py` `|rich` (bleach; only
  `khatt.org` `<img>` allowed). `Answer.text`/`ScoreAnswer` snapshot fields are
  1000 chars to fit embedded image tags. Repository location chosen at render
  time by `core/context_processors.py` (`math_engine` = `khatt` iff lang == ar)
- i18n: bilingual en/ar. Server side uses a custom dictionary in
  `core/translations.py` (`AR` map + `t(text, lang=...)` / `get_translations_json`)
  exposed via `core/templatetags/i18n_tags.py` (`{% tr %}`, `{% trf %}` with
  interpolation) and `core/context_processors.language_context` (sets
  `LANGUAGE_CODE`, `dir`, and the `QUIZ_L10N_JSON` JS blob). Language switch is
  Django's built-in `set_language` (POST `language` + `next`, navbar dropdown).
  Client side loads `window.QUIZ_LANG` + `window.QUIZ_L10N` from the blob and a
  global `Q(key)` helper (defined in `base.html`); all page scripts
  (quiz_taker/quiz_builder/ai_explainer/latex_helper) render via `Q()`. RTL is
  applied through `<html dir="rtl">` + Bootstrap RTL CSS when lang=ar. The AI
  explanation prompt is language-aware (`build_prompt(..., lang=)`). Auth form
  labels (Username/Password/Password confirmation) are localized in
  `accounts/forms.py` via the same `t()` helper (`LoginForm`, `RegisterForm`).

## [SYSTEM_FLOW]
1. Browse: `/` (categories) -> `/categories/<pk>/` (quizzes, lock badge on private)
2. Private quiz: `/quizzes/<pk>/` shows access gate -> POST `/quizzes/<pk>/access/`
   verifies code, grants session flag (applies to guests AND users)
3. Take: one-question panels -> radio change POSTs `/api/quizzes/<id>/answers/`
   (guest -> session store, auth -> SelectedAnswer row) -> Submit blocked while
   unanswered; POST `/api/quizzes/<id>/submit/` computes earned/total/correct
4. Attempts: auth users may submit up to 3 times (`scoring.services.MAX_ATTEMPTS`).
   Each submit writes a `Score` (unique `(user, quiz, attempt_number)`) plus one
   `ScoreAnswer` per question (snapshot of question/answer text, correct answer
   text, points, is_correct). Guests keep a single session lock. "Start attempt
   N" (POST `/quizzes/<pk>/restart/`) clears in-progress selections and sets a
   session `quiz_started` flag so the take page shows the widget again; submit
   clears the flag. Revisit with a Score (and no in-progress attempt) shows the
   submitted panel: latest score, Review link, start button, or "all attempts
   used" when exhausted. Further saves/submits after 3 attempts return 409
5. Review/history (auth): `/scores/` lists every attempt (quiz, attempt #,
   score, Review link); `/scores/<pk>/` is the per-attempt review page — your
   answer + correct answer (green/red) + points earned, per question, with
   "Ask AI" (passes `score_id`; ownership checked, else 404)
6. Create (auth): `/quizzes/new/` dynamic Q/A rows -> create_quiz service
   validates (>=1 q, <=50 q, >=2 answers, >=1 correct, private needs code);
   per-question "Math" toggle persists `Question.math_enabled`; the active
   language picks the engine — Arabic shows the Khatt symbol palette + live
   preview (debounced, `<img>` tags inserted via `khatt_helper.js`, `.khatt-content`
   preview box), English shows the KaTeX template guide + live preview
   (LaTeX `$`/`$$`/`\(`/`\[` delimiters, flags `.katex-error` before save);
   pasting a copied template inside an existing math region strips redundant
   delimiters via `LaTeXHelper.mergeMath` (paste handler in quiz_builder.js);
   total points = SUM(question.points) computed on read
6. AI: POST `/api/questions/<id>/ai-explain/` -> build_prompt -> Ollama Cloud
   (OLLAMA_HOST/v1/chat/completions, OLLAMA_MODEL, Bearer OLLAMA_API_KEY)
   -> markdown -> bleach.clean -> HTML; 503 on missing key / HTTP error.
   Optional `score_id` body param makes the prompt use that attempt's chosen
   answer (ScoreAnswer lookup, ownership-checked); used on the review page
7. Math: engine follows `LANGUAGE_CODE` (Arabic -> Khatt, else KaTeX). Khatt
   questions render their embedded sanitized `<img>` server-side via `|rich`;
   no KaTeX asset is loaded in Arabic. LaTeX questions load KaTeX (only when
   the quiz has any `math_enabled` question); `static/js/math_render.js`
   renders `.math-content` spans (`{throwOnError:false}`); AI explanations are
   re-rendered via auto-render in `ai_explainer.js` (sends `score_id` when
   `data-score-id` is present). Khatt `<img>` tags are stripped to
   `[formula: alt]` before building the LLM prompt (`ai_feedback/services.py`)
8. My Scores (auth): `/scores/` lists Score rows; `/scores/<pk>/` review page
     (`ScoreDetailView`, ownership via `user=self.request.user`)
  9. Language: every page renders in the active language (en default, ar RTL).
     Navbar globe dropdown POSTs to `set_language` (`language`+`next`); the
     session language drives `{% tr %}`/`{% trf %}` in templates and the `Q()`
     helper in JS. The AI explanation honors the same language.
 10. Offline download (auth): GET `/quizzes/<pk>/download/` (
     `QuizDownloadView`) renders the quiz through
     `quizzes/offline.render_offline_quiz(quiz, lang)` into one self-contained
     HTML file and returns it as an attachment
     (`Content-Disposition: attachment; filename="<slug>-quiz.html"`). Private
     quizzes require the session access grant (same gate as the take page).
     The file bundles `static/css/offline_quiz.css` + `offline_quiz.js` inline,
     KaTeX (JS/CSS/woff2 fonts fetched from jsdelivr and inlined) when the quiz
     has LaTeX math and the UI is not Arabic, khatt.org images and uploaded
     question images as base64 `data:` URIs, and an `OFFLINE_I18N` JSON of the
     translated labels. Local scoring reads `data-correct` attributes on the
     radios; answers/timer resume from `localStorage` (`offline_quiz_<id>`).
     Download links are on the take page sidebar + submitted card, the score
     list rows, and the score-detail review page.

## [ARCHITECTURE]
- 5 feature apps + 1 shared:
  - `core`: QuizSessionStore (guest answers/locks + access flags), non-blocking
    logging (QueueHandler+QueueListener in AppConfig.ready), seed_demo command;
    i18n support — `translations.py`, `templatetags/i18n_tags.py`,
    `context_processors.py` (language_context), JS L10N blob
  - `accounts`: register/login/logout (Django auth)
  - `catalog`: Category + browse views, selectors
  - `quizzes`: Quiz/Question/Answer models, take/create UI, services (create_quiz),
    selectors (quiz_total_points, prefetch helpers), offline export service
    (quizzes/offline.py: `_fetch_bytes` w/ manual cache for tests, `_embed_khatt`,
    `_katex_assets`, `_image_data_uri`, `render_offline_quiz`), admin w/ inlines
  - `scoring`: Score + ScoreAnswer + SelectedAnswer models, services (record_answer,
    submit_quiz, start_attempt, compute_score, MAX_ATTEMPTS), selectors
    (selected_map, user_scores, user_attempts), DRF api.py, My Scores + review views
  - `ai_feedback`: services (build_prompt, ask_for_explanation, markdown_to_html), DRF view
- Layers: views/viewsets thin -> services.py (mutations) / selectors.py (reads)
- Config: `config/` package (settings, urls, wsgi, asgi), secrets via env
- Static: `static/js/` quiz_taker.js, quiz_builder.js, ai_explainer.js,
  math_render.js, latex_helper.js, khatt_helper.js, offline_quiz.js;
  `static/css/arabic.css` (khatt palette + `.khatt-content img` styles),
  `static/css/offline_quiz.css` (design tokens + mini-Bootstrap subset for the
  standalone offline file)
- Templates: `templates/` base + per-app templates; sanitized rich-text filter
  in `quizzes/templatetags/quiz_filters.py` (`|rich`)

## [ORPHANS & PENDING]
- No orphans. Greenfield, fully implemented.
- Pending (user action):
  - Set `OLLAMA_API_KEY` in `.env` (create at https://ollama.com/settings/keys)
    to enable AI feedback; adjust `OLLAMA_MODEL` if the default isn't available
    to your account (see https://ollama.com/search?c=cloud)
  - Set a real `SECRET_KEY` in production
- Note: deleting a question while an image is attached loses that image upload
  in the create form (JS rebuild limitation) — acceptable, not blocking
- Note: Django auth form `help_text` (e.g. password rules) is not yet translated
  (labels and error messages are via the AR dict) — acceptable, not blocking
- Note: `seed_demo` is intentionally non-idempotent (existing behavior); re-running
  it duplicates quizzes. A one-off "Math & Physics Basics" quiz (LaTeX demo) was
  seeded into the current dev DB.
