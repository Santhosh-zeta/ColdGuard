import React from "react";
import { View, Text, StyleSheet } from "react-native";

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
 *   decision  {string}  "USE" | "INVESTIGATE" | "DISCARD"
 *   message   {string}  Short explanation text
 *   confidence {number} 0–1
 */
export default function DecisionBanner({ decision, message, confidence }) {
  const style = STYLES[decision] || STYLES.INVESTIGATE;

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: style.background, borderColor: style.border },
      ]}
    >
      <Text style={styles.emoji}>{style.emoji}</Text>
      <Text style={[styles.decision, { color: style.text }]}>{decision}</Text>
      {confidence !== undefined && (
        <Text style={[styles.confidence, { color: style.text }]}>
          Confidence: {(confidence * 100).toFixed(0)}%
        </Text>
      )}
      {message ? (
        <Text style={[styles.message, { color: style.text }]}>{message}</Text>
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
