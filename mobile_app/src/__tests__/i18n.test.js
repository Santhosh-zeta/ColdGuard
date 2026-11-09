/**
 * Ensures every language file exposes exactly the same keys as en.js.
 * Nested objects (e.g. `vaccines`) are flattened to dotted paths.
 */

import en from "../i18n/en";
import hi from "../i18n/hi";
import ta from "../i18n/ta";
import bn from "../i18n/bn";
import te from "../i18n/te";
import kn from "../i18n/kn";

const flattenKeys = (obj, prefix = "") =>
  Object.entries(obj).flatMap(([key, value]) =>
    value && typeof value === "object"
      ? flattenKeys(value, `${prefix}${key}.`)
      : [`${prefix}${key}`]
  );

const EN_KEYS = new Set(flattenKeys(en));

const LANGUAGES = { hi, ta, bn, te, kn };

describe("i18n key parity with en", () => {
  it("en defines a non-empty key set", () => {
    expect(EN_KEYS.size).toBeGreaterThan(0);
  });

  it.each(Object.keys(LANGUAGES))("%s has exactly the same keys as en", lang => {
    const keys = new Set(flattenKeys(LANGUAGES[lang]));
    const missing = [...EN_KEYS].filter(k => !keys.has(k));
    const extra = [...keys].filter(k => !EN_KEYS.has(k));
    expect({ missing, extra }).toEqual({ missing: [], extra: [] });
  });
});
