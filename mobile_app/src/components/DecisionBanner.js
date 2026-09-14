import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { useTranslation } from "../i18n/useTranslation";

const STYLES = {
  USE: {
    background: "#E8F5E9",
    border: "#4CAF50",
    text: "#1B5E20",
    emoji: "✅",
  },
  INVESTIGATE: {
    background: "#FFF3E0",
    border: "#FF9800",
    text: "#E65100",
    emoji: "⚠️",
  },
  DISCARD: {
    background: "#FFEBEE",
    border: "#F44336",
    text: "#B71C1C",
    emoji: "🚫",
  },
};

/**
 * DecisionBanner
 *
 * Props:
 *   decision   {string|object} "USE" | "INVESTIGATE" | "DISCARD" or { decision, confidence, explanation }
 *   message    {string}        Short explanation text
 *   confidence {number}        0–1
 *   posterior  {object}        Optional posterior summary
 */
export default function DecisionBanner({ decision, message, confidence, posterior }) {
  const { t } = useTranslation();

  const decKey = (typeof decision === "object" && decision !== null)
    ? decision.decision
    : decision;
  const normalizedKey = (decKey || "INVESTIGATE").toUpperCase();
  const style = STYLES[normalizedKey] || STYLES.INVESTIGATE;

  const confVal = confidence !== undefined
    ? confidence
    : (typeof decision === "object" && decision !== null
        ? decision.confidence
        : (posterior ? (posterior.probAbove80 ?? posterior.prob_above_80pct) : undefined));

  const displayDecision = t(normalizedKey.toLowerCase()) || normalizedKey;
  const displayMsg = message || (typeof decision === "object" && decision !== null
    ? decision.explanation
    : t(`${normalizedKey.toLowerCase()}Message`));

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: style.background, borderColor: style.border },
      ]}
    >
      <Text style={styles.emoji}>{style.emoji}</Text>
      <Text style={[styles.decision, { color: style.text }]}>{displayDecision}</Text>
      {confVal !== undefined && (
        <Text style={[styles.confidence, { color: style.text }]}>
          {t("confidence")}: {(confVal * 100).toFixed(0)}%
        </Text>
      )}
      {displayMsg ? (
        <Text style={[styles.message, { color: style.text }]}>{displayMsg}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderWidth: 2,
    borderRadius: 12,
    padding: 20,
    alignItems: "center",
    marginVertical: 12,
  },
  emoji: {
    fontSize: 40,
    marginBottom: 8,
  },
  decision: {
    fontSize: 28,
    fontWeight: "bold",
    letterSpacing: 1,
  },
  confidence: {
    fontSize: 16,
    marginTop: 4,
  },
  message: {
    fontSize: 14,
    textAlign: "center",
    marginTop: 10,
    lineHeight: 20,
  },
});
