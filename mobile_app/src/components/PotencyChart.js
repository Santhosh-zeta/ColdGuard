import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

/**
 * Simple horizontal bar chart showing mean potency with CI bounds.
 * Avoids external charting libraries for offline compatibility.
 */
export default function PotencyChart({ posterior, threshold }) {
  const mean = posterior.mean;
  const lo = posterior.ci90Lower;
  const hi = posterior.ci90Upper;

  const BAR_WIDTH = 280;
  const meanPx = mean * BAR_WIDTH;
  const loPx = lo * BAR_WIDTH;
  const hiPx = hi * BAR_WIDTH;
  const threshPx = threshold * BAR_WIDTH;

  const barColor = mean >= threshold ? '#2e7d32' : mean >= threshold * 0.9 ? '#f57f17' : '#c62828';

  return (
    <View style={styles.container}>
      <View style={[styles.track, { width: BAR_WIDTH }]}>
        {/* CI band */}
        <View style={[styles.ciBar, { left: loPx, width: hiPx - loPx }]} />
        {/* Mean bar */}
        <View style={[styles.meanBar, { width: meanPx, backgroundColor: barColor }]} />
        {/* Threshold line */}
        <View style={[styles.threshLine, { left: threshPx }]} />
      </View>
      <View style={[styles.labels, { width: BAR_WIDTH }]}>
        <Text style={styles.labelText}>0%</Text>
        <Text style={styles.labelText}>{(threshold * 100).toFixed(0)}% min</Text>
        <Text style={styles.labelText}>100%</Text>
      </View>
      <Text style={styles.summary}>
        {(mean * 100).toFixed(1)}% ({(lo * 100).toFixed(1)}–{(hi * 100).toFixed(1)}% CI90)
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'flex-start', paddingVertical: 8 },
  track: { height: 24, backgroundColor: '#e0e0e0', borderRadius: 12, overflow: 'hidden', position: 'relative' },
  ciBar: { position: 'absolute', top: 0, bottom: 0, backgroundColor: 'rgba(21,101,192,0.2)' },
  meanBar: { position: 'absolute', top: 0, bottom: 0, left: 0, borderRadius: 12 },
  threshLine: { position: 'absolute', top: 0, bottom: 0, width: 2, backgroundColor: '#f44336' },
  labels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  labelText: { fontSize: 11, color: '#666' },
  summary: { marginTop: 8, fontSize: 15, fontWeight: '600', color: '#333' },
});
