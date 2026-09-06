import json
from django.conf import settings
from django.utils.safestring import SafeData, mark_safe

# Supported languages
LANGUAGES = {
    "en": "English",
    "ar": "العربية",
}

# Arabic translations: { English Source: Arabic Translation }
# These cover template literals, Python messages, and JS strings
AR = {
    # --- Navbar / Base ---
    "Hi, {username}": "مرحباً، {username}",
    "My Scores": "نتائجي",
    "New Quiz": "اختبار جديد",
    "Log out": "تسجيل الخروج",
    "Log in": "تسجيل الدخول",
    "Register": "إنشاء حساب",
    "Quiz Platform": "منصة الاختبارات",
    "Home": "الرئيسية",
    "Toggle theme": "تبديل السمة",
    "Skip to content": "تخطَّ إلى المحتوى",
    "Welcome back, {username}!": "مرحباً بعودتك، {username}!",
    "Test & Educate Yourself Now!": "اختبر وعلم نفسك الآن!",
    "Browse our library of educational quizzes and put your knowledge to the test.": "تصفح مكتبتنا من الاختبارات التعليمية واختبر معلوماتك.",
    "Get Started": "ابدأ الآن",
    "Start Quizzing": "ابدأ الاختبار",
    "Pick a category to begin": "اختر فئة للبدء",
    "Your selections are saved automatically as you go.": "يتم حفظ اختياراتك تلقائياً أثناء إجابتك.",
    "Review your submitted attempts, one page per quiz.": "راجع محاولاتك المسلّمة، صفحة لكل اختبار.",
    "Full marks": "درجة كاملة",
    "Partial score": "درجة جزئية",

    # --- Catalog ---
    "Categories": "الفئات",
    "Quizzes in {category}": "الاختبارات في {category}",
    "Browse Quizzes": "تصفح الاختبارات",
    "Private": "خاص",
    "quiz": "اختبار",
    "quizzes": "اختبارات",
    "question": "سؤال",
    "s": "",
    "No quizzes in this category yet.": "لا توجد اختبارات في هذه الفئة بعد.",
    "No categories yet. Run `python manage.py seed_demo` to add sample data.": "لا توجد فئات بعد. شغّل `python manage.py seed_demo` لإضافة بيانات تجريبية.",

    # --- Quiz Create ---
    "Create Quiz": "إنشاء اختبار",
    "Create a Quiz": "إنشاء اختبار",
    "Quiz title": "عنوان الاختبار",
    "Category": "الفئة",
    "Select…": "اختر…",
    "e.g. QUIZ123": "مثال: QUIZ123",
    "is_public": "عام",
    "Public": "عام",
    "access_code": "رمز الدخول",
    "Quiz title is required.": "عنوان الاختبار مطلوب.",
    "Please choose a category.": "يرجى اختيار فئة.",
    "questions": "الأسئلة",
    "answers": "الإجابات",
    "Time limit (minutes)": "الوقت المحدد (بالدقائق)",
    "Enable time limit": "تفعيل الوقت المحدد",
    "Optional (1-180)": "اختياري (1-180)",
    "min": "دقيقة",
    "Time limit must be a whole number of minutes.": "يجب أن يكون الوقت المحدد رقماً صحيحاً بالدقائق.",
    "Time limit must be between 1 and {n} minutes.": "يجب أن يكون الوقت المحدد بين 1 و {n} دقيقة.",
    "points": "نقاط",
    "Math (LaTeX)": "رياضيات (LaTeX)",
    "Math (Arabic)": "رياضيات عربية",
    "Symbols & templates": "الرموز والقوالب",
    "Insert": "إدراج",
    "Preview": "معاينة",
    "Raw command": "الأمر",
    "Symbols": "الرموز",
    "Reset fields": "إعادة الحقول",
    "Render the question and its answers as LaTeX (via KaTeX).": "عرض السؤال وإجاباته باستخدام LaTeX (عبر KaTeX).",
    "Optional time limit in whole minutes (1-180) for taking the quiz.": "وقت محدد بالدقائق الكاملة (1-180) لإجراء الاختبار.",
    "Submit quiz": "إرسال الاختبار",
    "Save": "حفظ",
    "Cancel": "إلغاء",

    # --- Quiz Take ---
    "Private Quiz": "اختبار خاص",
    "This quiz is private. Enter the access code to take it.": "هذا الاختبار خاص. أدخل رمز الدخول للمتابعة.",
    "Incorrect access code. Try again.": "رمز الدخول غير صحيح. حاول مرة أخرى.",
    "Unlock": "فتح",
    "Your score is locked in": "تم تثبيت درجتك",
    "You have already submitted this quiz and can no longer change your answers.": "لقد قمت بتسليم هذا الاختبار بالفعل ولا يمكنك تغيير إجاباتك.",
    "Total: {total} points": "المجموع: {total} نقطة",
    "Question {counter}": "سؤال {counter}",
    "pts": "نقطة",
    "Ask AI": "اسأل الذكاء الاصطناعي",
    "saved": "تم الحفظ",
    "Previous": "السابق",
    "Next": "التالي",
    "Submit quiz": "إرسال الاختبار",
    "Please answer all questions before submitting: {list}": "يرجى الإجابة على جميع الأسئلة قبل التسليم: {list}",
    "Thinking…": "جاري التفكير…",
    "Could not generate an explanation.": "تعذر إنشاء شرح.",

    # --- Scoring / Review ---
    "My Scores": "نتائجي",
    "Quiz": "الاختبار",
    "Category": "الفئة",
    "Score": "الدرجة",
    "Completed": "تاريخ الإكمال",
    "Review": "مراجعة",
    "Review: {title}": "مراجعة: {title}",
    "Attempt {number} of {total} submitted": "تم تسليم المحاولة {number} من {total}",
    "Your score for this attempt is locked in.": "درجتك لهذه المحاولة مثبتة.",
    "Review answers": "مراجعة الإجابات",
    "Start attempt {next} of {total}": "بدء المحاولة {next} من {total}",
    "You have used all {total} attempts.": "لقد استنفدت جميع محاولاتك ({total}).",
    "Your answer: {value}": "إجابتك: {value}",
    "Correct answer: {value}": "الإجابة الصحيحة: {value}",
    "All my scores": "جميع نتائجي",
    "Take again": "إعادة المحاولة",

    # --- Quiz Take (continued) ---
    "Take Quiz": "خوض الاختبار",
    "Time Remaining": "الوقت المتبقي",
    "Time's up! Your answers were submitted.": "انتهى الوقت! تم إرسال إجاباتك.",
    "Submit": "إرسال",
    "Required": "مطلوب",
    "Mark as correct": "تحديد كإجابة صحيحة",
    "Correct": "صحيح",
    "Your answer": "إجابتك",
    "Correct answer": "الإجابة الصحيحة",
    "Explanation": "الشرح",
    "Check": "تحقق",
    "You reached the end of the quiz.": "لقد وصلت إلى نهاية الاختبار.",
    "Review summary": "مراجعة الملخص",
    "Your score": "درجتك",
    "correct": "صحيحة",
    "Retake quiz": "إعادة الاختبار",
    "Detailed results": "النتائج التفصيلية",
    "Question": "سؤال",
    "Correct?": "صحيحة؟",
    "Yes": "نعم",
    "No": "لا",
    "of": "من",

    # --- Score list / detail ---
    "Attempt": "المحاولة",
    "Attempt {number}": "المحاولة {number}",
    "You haven't submitted any quizzes yet.": "لم ترسل أي اختبارات بعد.",
    "Browse quizzes": "تصفح الاختبارات",
    "No attempt details are available for this older score.": "لا تتوفر تفاصيل للمحاولة لهذه النتيجة القديمة.",

    # --- Quiz builder (client-side JS) ---
    "Points": "النقاط",
    "Optional image": "صورة اختيارية",
    "Add answer": "إضافة إجابة",
    "LaTeX guide & templates": "دليل ومقتطفات LaTeX",
    "Live preview": "معاينة فورية",
    "Remove question": "حذف السؤال",
    "Add question": "إضافة سؤال",
    "Answer text": "نص الإجابة",
    "Maximum 50 questions reached.": "تم الوصول إلى الحد الأقصى وهو 50 سؤالاً.",
    "Save quiz": "حفظ الاختبار",
    "Please add at least one question.": "يرجى إضافة سؤال واحد على الأقل.",
    "Each question must have at least two answers.": "يجب أن يحتوي كل سؤال على إجابتين على الأقل.",
    "Please mark exactly one correct answer per question.": "يرجى تحديد إجابة صحيحة واحدة فقط لكل سؤال.",
    "Please provide question text.": "يرجى إدخال نص السؤال.",
    "Some formulas contain errors and may not render correctly.": "بعض المعادلات تحتوي على أخطاء وقد لا تظهر بشكل صحيح.",
    "Copied!": "تم النسخ!",
    "Copy": "نسخ",

    # --- AI explainer (client-side JS) ---
    "Asking AI…": "جاري سؤال الذكاء الاصطناعي…",

    # --- Accounts ---
    "No account?": "ليس لديك حساب؟",
    "Create account": "إنشاء حساب",
    "Already have an account?": "لديك حساب بالفعل؟",
    "Welcome back — test and educate yourself.": "مرحباً بعودتك — اختبر وتعلّم نفسك.",
    "Create your account to start your journey.": "أنشئ حسابك لتبدأ رحلتك.",
    "Username": "اسم المستخدم",
    "Password": "كلمة المرور",
    "Password confirmation": "تأكيد كلمة المرور",

    # --- Service validation messages ---
    "Public quizzes require an access code.": "الاختبارات العامة تتطلب رمز دخول.",
    "Access-code quizzes must be marked public.": "يجب أن تكون اختبارات رمز الدخول عامة.",
    "A quiz must have at least one question.": "يجب أن يحتوي الاختبار على سؤال واحد على الأقل.",
    "A quiz can have at most {n} questions.": "يمكن أن يحتوي الاختبار على {n} سؤالاً كحد أقصى.",
    "A private quiz requires an access code.": "الاختبار الخاص يتطلب رمز دخول.",
    "Question {n}: text is required.": "سؤال {n}: النص مطلوب.",
    "Question {n}: points must be a number.": "سؤال {n}: يجب أن تكون النقاط رقماً.",
    "Question {n}: points must be at least 1.": "سؤال {n}: يجب أن تكون النقاط 1 على الأقل.",
    "Question {n}: at least {m} answers are required.": "سؤال {n}: مطلوب {m} إجابات على الأقل.",
    "Question {n}, answer {m}: text is required.": "سؤال {n}، إجابة {m}: النص مطلوب.",
    "Question {n}: at least one answer must be marked correct.": "سؤال {n}: يجب تحديد إجابة صحيحة واحدة على الأقل.",

    # --- Quiz Take (template-only literals) ---
    "Access code": "رمز الدخول",
    "Back to categories": "العودة إلى الفئات",
    "Question image": "صورة السؤال",
    "points total": "نقطة إجمالية",
    "Please answer all questions before submitting:": "يرجى الإجابة على جميع الأسئلة قبل التسليم:",
    "You have used all {total} attempts for this quiz.": "لقد استنفدت جميع محاولاتك ({total}) لهذا الاختبار.",

    # --- Offline quiz download ---
    "Download": "تحميل",
    "Download quiz (offline)": "تحميل الاختبار (للاستخدام دون اتصال)",
    "Offline practice file — answers are saved in this browser only, not to the server.": "ملف تدريب دون اتصال — تُحفظ الإجابات في هذا المتصفح فقط، وليس على الخادم.",
    "Not answered": "لم تتم الإجابة",
    "Your score: {earned} / {total}": "درجتك: {earned} / {total}",
    "Correct answers: {correct} of {total}": "الإجابات الصحيحة: {correct} من {total}",

    # --- Quiz builder / taker (client-side JS, exact strings) ---
    "Question text": "نص السؤال",
    "Some formulas contain errors. Fix them before saving.": "بعض المعادلات تحتوي على أخطاء. صححها قبل الحفظ.",
    "Maximum {n} questions.": "الحد الأقصى {n} سؤالاً.",
    "Submitting…": "جاري الإرسال…",
    "Could not submit: ": "تعذر الإرسال: ",
    "Unexpected error.": "خطأ غير متوقع.",

    # --- API error detail messages ---
    "Quiz not found.": "الاختبار غير موجود.",
    "Access code required.": "رمز الدخول مطلوب.",
    "Already submitted.": "تم التسليم مسبقاً.",
    "Not all questions are answered.": "لم يتم الإجابة على جميع الأسئلة.",
}

def _interp(template_str, kwargs):
    """Interpolate kwargs, keeping the result marked-safe if any interpolated
    value is already safe (e.g. HTML markup produced by the ``rich`` filter).

    ``str.format`` downgrades ``SafeString`` values to plain ``str``, so the
    final auto-escape in templates would re-escape embedded HTML and show it
    as literal text. Re-marking the result as safe fixes that while leaving
    plain-text interpolations (numbers, usernames, LaTeX source) unchanged.
    """
    if not kwargs:
        return template_str
    result = template_str.format(**kwargs)
    if any(isinstance(v, SafeData) for v in kwargs.values()):
        return mark_safe(result)
    return result


def t(text, lang="en", **kwargs):
    """Translate a string based on the current language."""
    if lang != "ar":
        return _interp(text, kwargs)

    translated = AR.get(text, text)
    return _interp(translated, kwargs)

def get_translations_json(lang):
    """Return the translation dictionary for JS injection."""
    if lang == "ar":
        return json.dumps(AR, ensure_ascii=False)
    return json.dumps({})
