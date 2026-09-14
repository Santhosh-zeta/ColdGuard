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
    """Verify that en.js, hi.js, ta.js, bn.js, te.js, and kn.js all exist."""
    for lang in ["en", "hi", "ta", "bn", "te", "kn"]:
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


def test_all_twelve_vaccines_present_in_telugu():
    """Verify that all 12 UIP vaccines (including YF, JE, Typhoid, MenA) are in te.js."""
    expected_vaccines = {
        "DPT", "OPV", "MMR", "BCG", "HepB", "IPV",
        "Rotavirus", "PCV", "YF", "JE", "Typhoid", "MenA"
    }
    _, te_vax, _ = parse_js_dict_keys(os.path.join(I18N_DIR, "te.js"))
    missing = expected_vaccines - te_vax
    assert not missing, f"te.js is missing vaccines: {missing}"


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


def test_kannada_keys_match_english():
    """Verify that all keys in en.js are implemented in kn.js."""
    en_keys, en_vax, _ = parse_js_dict_keys(os.path.join(I18N_DIR, "en.js"))
    kn_keys, kn_vax, _ = parse_js_dict_keys(os.path.join(I18N_DIR, "kn.js"))

    missing_keys = en_keys - kn_keys
    assert not missing_keys, f"kn.js is missing top-level keys from en.js: {missing_keys}"

    missing_vax = en_vax - kn_vax
    assert not missing_vax, f"kn.js is missing vaccine names from en.js: {missing_vax}"


def test_all_twelve_vaccines_present_in_kannada():
    """Verify that all 12 UIP vaccines are present in kn.js."""
    expected_vaccines = {
        "DPT", "OPV", "MMR", "BCG", "HepB", "IPV",
        "Rotavirus", "PCV", "YF", "JE", "Typhoid", "MenA"
    }
    _, kn_vax, _ = parse_js_dict_keys(os.path.join(I18N_DIR, "kn.js"))
    missing = expected_vaccines - kn_vax
    assert not missing, f"kn.js is missing vaccines: {missing}"


def test_kannada_medical_translations():
    """Verify critical medical and clinical terminology in kn.js."""
    _, _, kn_content = parse_js_dict_keys(os.path.join(I18N_DIR, "kn.js"))

    required_terms = [
        "estimatedPotency",
        "confidenceInterval",
        "freezeWarning",
        "useMessage",
        "discardMessage",
        "investigateMessage",
    ]

    for term in required_terms:
        assert term in kn_content, f"kn.js missing key: {term}"

    # Verify Kannada script is present in translations
    kannada_range_match = re.search(r'[\u0C80-\u0CFF]', kn_content)
    assert kannada_range_match is not None, "kn.js does not contain Kannada Unicode characters"


def test_use_translation_registration():
    """Verify that all languages including kn are imported and registered in useTranslation.js."""
    path = os.path.join(I18N_DIR, "useTranslation.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    for lang in ["en", "hi", "ta", "bn", "te", "kn"]:
        assert f"import {lang} from './{lang}';" in content or f"import {lang} from './{lang}'" in content
        assert lang in content

    assert re.search(r'TRANSLATIONS\s*=\s*\{[^}]*kn[^}]*\}', content) is not None


def test_app_js_language_toggle():
    """Verify that App.js registers all 6 languages including 'kn' in its language cycle."""
    app_js_path = os.path.join(MOBILE_APP_DIR, "App.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    for lang in ["en", "hi", "ta", "bn", "te", "kn"]:
        assert f"'{lang}'" in content or f'"{lang}"' in content


def test_all_vaccines_present_across_languages():
    """Verify that all 12 UIP vaccines are present in en, hi, ta, bn, te, and kn."""
    expected_vaccines = {
        "DPT", "OPV", "MMR", "BCG", "HepB", "IPV",
        "Rotavirus", "PCV", "YF", "JE", "Typhoid", "MenA"
    }
    for lang in ["en", "hi", "ta", "bn", "te", "kn"]:
        _, vax_keys, _ = parse_js_dict_keys(os.path.join(I18N_DIR, f"{lang}.js"))
        missing = expected_vaccines - vax_keys
        assert not missing, f"Missing vaccines in {lang}.js: {missing}"


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
