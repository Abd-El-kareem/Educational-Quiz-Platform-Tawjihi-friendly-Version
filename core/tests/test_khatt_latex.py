from core.khatt_latex import (
    formula_marker,
    khatt_command_from_src,
    to_latex,
)


def latex(command):
    text, unknown = to_latex(command)
    return text, unknown


def test_fraction():
    assert latex("/على {س + 1} {2}") == (r"\frac{x + 1}{2}", False)


def test_nested_fraction_and_sqrt():
    assert latex(r"/على {1} {/جذر {2}}") == (r"\frac{1}{\sqrt{2}}", False)


def test_nth_root():
    assert latex("/جذر {3} {8}") == (r"\sqrt[3]{8}", False)


def test_power():
    assert latex("/على {س} {ب}") == (r"\frac{x}{b}", False)


def test_power_of_group():
    text, unknown = latex("{س + 1}^{2}")
    assert text == "{x + 1} ^ {2}"
    assert not unknown


def test_power_of_literal():
    assert latex("{ب}^{2}") == (r"{b} ^ {2}", False)


def test_sum():
    assert latex("/مج {س + 1} {ص + 1}") == (r"\sum_{x + 1}^{y + 1}", False)


def test_integral():
    assert latex("/تكا {0} {1}") == (r"\int_{0}^{1}", False)


def test_limit():
    assert latex("/نها {س} {3}") == (r"\lim_{3}{x}", False)


def test_large_fraction():
    assert latex("/على {3} {2}") == (r"\frac{3}{2}", False)


def test_bracket():
    assert latex("( 1 + 3 )") == (r"\left( 1 + 3 \right)", False)


def test_square_bracket():
    assert latex("[ 1 + 2 ]") == (r"\left[ 1 + 2 \right]", False)


def test_fraction_chain():
    assert latex("/على {س} {/على {1} {2}}") == (r"\frac{x}{\frac{1}{2}}", False)


def test_symbols_times():
    assert latex("/.ضرب") == (r"\times", False)


def test_symbols_plusminus():
    assert latex("/.زائد.ناقص") == (r"\pm", False)


def test_symbols_div():
    assert latex("/.قسمة") == (r"\div", False)


def test_symbols_pi():
    assert latex("/.باي") == (r"\pi", False)


def test_symbols_infinity():
    assert latex("/.لا.نهاية") == (r"\infty", False)


def test_symbols_in():
    assert latex("/.ينتمي") == (r"\in", False)


def test_symbols_empty():
    assert latex("/.خالية") == (r"\emptyset", False)


def test_symbols_exists():
    assert latex("/.يوجد") == (r"\exists", False)


def test_symbols_forall():
    assert latex("/.لكل") == (r"\forall", False)


def test_symbols_gte():
    assert latex("/.أكبر.يساوي") == (r"\geq", False)


def test_symbols_lte():
    assert latex("/.أصغر.يساوي") == (r"\leq", False)


def test_symbols_neq():
    assert latex("/.لا.يساوي") == (r"\neq", False)


def test_symbols_approx():
    assert latex("/.يساوي.تقريبا") == (r"\approx", False)


def test_symbols_subset():
    assert latex("/.جزئي.فعلي") == (r"\subset", False)


def test_symbols_subseteq():
    assert latex("/.جزئي.يساوي") == (r"\subseteq", False)


def test_symbols_rightarrow():
    assert latex("/.سهم.يمين") == (r"\rightarrow", False)


def test_symbols_Rightarrow():
    assert latex("/.سهم.يمين.مزدوج") == (r"\Rightarrow", False)


def test_symbols_leftarrow():
    assert latex("/.سهم.يسار") == (r"\leftarrow", False)


def test_symbols_Leftarrow():
    assert latex("/.سهم.يسار.مزدوج") == (r"\Leftarrow", False)


def test_symbols_land():
    assert latex("/.و") == (r"\land", False)


def test_symbols_lor():
    assert latex("/.أو") == (r"\lor", False)


def test_symbols_union():
    assert latex("/.اتحاد") == (r"\cup", False)


def test_symbols_intersection():
    assert latex("/.تقاطع") == (r"\cap", False)


def test_symbols_circ():
    assert latex("/.عامل.الدائرة") == (r"\circ", False)


def test_overset():
    assert latex("/فوق {س} {5}") == (r"\overset{5}{x}", False)


def test_underset():
    assert latex("/تحت {س} {5}") == (r"\underset{5}{x}", False)


def test_cancel():
    assert latex("/شخط {2}") == (r"\cancel{2}", False)


def test_ignore_layout_commands():
    text, unknown = latex("/سطر {/فراغ {س}}")
    assert text == ""
    assert not unknown


def test_quoted_string():
    assert latex('"س + 1"') == ("س + 1", False)


def test_unknown_command_raw():
    text, unknown = latex("/مجموع {س}")
    assert text == "مجموع x"
    assert unknown


def test_unknown_symbol_raw():
    text, unknown = latex("/.ليس")
    assert text == "ليس"
    assert unknown


def test_unknown_preserves_raw_fallback():
    assert formula_marker("/مجموع {س}") == "[formula: مجموع x; raw: /مجموع {س}]"


def test_option_command_skipped():
    assert latex("/على {س} {2} #option") == (r"\frac{x}{2}", False)


def test_plus_sign_preserved_in_url():
    src = "https://khatt.org/api?c=/على%20%7Bes+1%7D%20%7B2%7D"
    assert khatt_command_from_src(src) == "/على {es+1} {2}"


def test_non_khatt_src_is_none():
    assert khatt_command_from_src("https://example.com/a.png") is None


def test_empty_src_is_none():
    assert khatt_command_from_src("") is None


def test_missing_c_param_is_none():
    assert khatt_command_from_src("https://khatt.org/api?x=1") is None


def test_formula_marker_no_unknown():
    assert formula_marker("/على {س + 1} {2}") == r"[formula: \frac{x + 1}{2}]"


def test_formula_marker_empty():
    assert formula_marker("") == "[formula]"


def test_gather():
    """One clean formula; no placeholders left as {0}."""
    marker = formula_marker("/على {س + 1} {2}")
    assert "{0}" not in marker
    assert "{arg" not in marker


def test_structure_matrix():
    assert latex("/مصفوفة {1} {2} \n{3} {4}") == (
        r"\begin{matrix}1 & 2 \\ 3 & 4\end{matrix}",
        False,
    )


def test_structure_column_enumeration():
    assert latex("/عمود {أ} {ب}") == (r"\begin{array}{c} a \\ b \end{array}", False)


def test_lo_khal():
    assert latex("/لو.خل {أحمر} {س}") == ("x", False)


def test_transliterate_single_letter():
    assert latex("س = 1") == ("x = 1", False)


def test_transliterate_adjacent_digit():
    assert latex("/على {2أ} {ب}") == (r"\frac{2a}{b}", False)


def test_transliterate_prose_untouched():
    assert latex("الجذر التربيعي") == ("الجذر التربيعي", False)


def test_transliterate_quadratic():
    src = "/على {-ب /.زائد.ناقص /جذر {{ب}^{2} - 4 أ ج}} {2أ}"
    text, unknown = latex(src)
    assert text == r"\frac{-b \pm \sqrt{{b} ^ {2} - 4 a c}}{2a}"
    assert not unknown