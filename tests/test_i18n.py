"""
Tests for mobile_app internationalization (i18n) and Telugu translations.
"""

import os
import re
import pytest

MOBILE_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mobile_app"))
I18N_DIR = os.path.join(MOBILE_APP_DIR, "src", "i18n")


def parse_js_dict_keys(file_path):
    """Simple parser to extract keys from an export default JS object."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find keys in the form of keyName: "..." or keyName: {
    keys = set(re.findall(r'^\s*([a-zA-Z0-9_]+)\s*:', content, re.MULTILINE))

    # Extract vaccines nested keys
    vaccines_match = re.search(r'vaccines:\s*\{([^}]+)\}', content, re.DOTALL)
    vaccine_keys = set()
    if vaccines_match:
        vaccine_keys = set(re.findall(r'([A-Za-z0-9_]+)\s*:', vaccines_match.group(1)))

    return keys, vaccine_keys, content


def test_i18n_files_exist():
    """Verify that en.js, hi.js, and te.js all exist."""
    for lang in ["en", "hi", "te"]:
        path = os.path.join(I18N_DIR, f"{lang}.js")
        assert os.path.isfile(path), f"Missing translation file: {path}"


def test_telugu_keys_match_english():
    """Verify that all keys in en.js are implemented in te.js."""
    en_keys, en_vax, _ = parse_js_dict_keys(os.path.join(I18N_DIR, "en.js"))
    te_keys, te_vax, _ = parse_js_dict_keys(os.path.join(I18N_DIR, "te.js"))

    missing_keys = en_keys - te_keys
    assert not missing_keys, f"te.js is missing top-level keys from en.js: {missing_keys}"

    missing_vax = en_vax - te_vax
    assert not missing_vax, f"te.js is missing vaccine names from en.js: {missing_vax}"


def test_telugu_medical_translations():
    """Verify critical medical and clinical terminology in te.js."""
    _, _, te_content = parse_js_dict_keys(os.path.join(I18N_DIR, "te.js"))

    required_terms = [
        "estimatedPotency",
        "confidenceInterval",
        "freezeWarning",
        "useMessage",
        "discardMessage",
        "investigateMessage",
    ]

    for term in required_terms:
        assert term in te_content, f"te.js missing key: {term}"

    # Verify Telugu script is present in translations
    telugu_range_match = re.search(r'[\u0C00-\u0C7F]', te_content)
    assert telugu_range_match is not None, "te.js does not contain Telugu Unicode characters"


def test_use_translation_registration():
    """Verify that te is imported and registered in useTranslation.js."""
    path = os.path.join(I18N_DIR, "useTranslation.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "import te from './te';" in content or "import te from './te'" in content
    assert re.search(r'TRANSLATIONS\s*=\s*\{[^}]*te[^}]*\}', content) is not None


def test_app_js_language_toggle():
    """Verify that App.js registers 'te' in its language cycle."""
    app_js_path = os.path.join(MOBILE_APP_DIR, "App.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "'te'" in content or '"te"' in content


def test_yf_vaccine_key_present():
    """Verify that Yellow Fever (YF) vaccine is present across en, hi, and te."""
    for lang in ["en", "hi", "te"]:
        _, vax_keys, _ = parse_js_dict_keys(os.path.join(I18N_DIR, f"{lang}.js"))
        assert "YF" in vax_keys, f"Missing YF vaccine key in {lang}.js"


def test_decision_banner_i18n_and_object_support():
    """Verify that DecisionBanner.js supports useTranslation and object decision props."""
    banner_path = os.path.join(MOBILE_APP_DIR, "src", "components", "DecisionBanner.js")
    with open(banner_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "useTranslation" in content
    assert "decKey" in content or "typeof decision === 'object'" in content or "typeof decision === \"object\"" in content


def test_input_screen_localized_vaccine_picker():
    """Verify that InputScreen.js renders localized vaccine names from t('vaccines')."""
    screen_path = os.path.join(MOBILE_APP_DIR, "src", "screens", "InputScreen.js")
    with open(screen_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "t('vaccines')" in content or 't("vaccines")' in content
