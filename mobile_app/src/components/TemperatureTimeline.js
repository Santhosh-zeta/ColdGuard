import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

const EXCURSION_THRESHOLD = 8.0;
const CHART_HEIGHT = 120;
const CHART_WIDTH = 300;

export default function TemperatureTimeline({ timestamps, temperatures }) {
  if (!timestamps || timestamps.length < 2) return null;

  const minT = Math.min(...temperatures) - 2;
  const maxT = Math.max(...temperatures) + 2;
  const tRange = maxT - minT || 1;
  const tRange2 = timestamps[timestamps.length - 1] - timestamps[0] || 1;

  // Build SVG-like path points
  const points = timestamps.map((ts, i) => ({
    x: ((ts - timestamps[0]) / tRange2) * CHART_WIDTH,
    y: CHART_HEIGHT - ((temperatures[i] - minT) / tRange) * CHART_HEIGHT,
    temp: temperatures[i],
    excursion: temperatures[i] > EXCURSION_THRESHOLD,
  }));

  return (
    <View style={styles.container}>
      <View style={[styles.chart, { width: CHART_WIDTH, height: CHART_HEIGHT }]}>
        {/* Excursion threshold line */}
        <View style={[styles.threshLine, {
          top: CHART_HEIGHT - ((EXCURSION_THRESHOLD - minT) / tRange) * CHART_HEIGHT,
          width: CHART_WIDTH,
        }]} />
        {/* Temperature dots */}
        {points.map((p, i) => (
          <View
            key={i}
            style={[
              styles.dot,
              { left: p.x - 3, top: p.y - 3 },
              p.excursion ? styles.dotHot : styles.dotNormal,
            ]}
          />
        ))}
      </View>
      <View style={styles.legend}>
        <View style={[styles.legendDot, styles.dotNormal]} /><Text style={styles.legendText}>Normal (≤8°C)</Text>
        <View style={[styles.legendDot, styles.dotHot]} /><Text style={styles.legendText}>Excursion (&gt;8°C)</Text>
      </View>
      <Text style={styles.range}>
        {temperatures.length} readings · {minT.toFixed(1)}–{maxT.toFixed(1)}°C
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingVertical: 8 },
  chart: { backgroundColor: '#f5f5f5', borderRadius: 8, position: 'relative', overflow: 'hidden' },
  threshLine: { position: 'absolute', height: 1, backgroundColor: '#f44336', opacity: 0.6 },
  dot: { position: 'absolute', width: 6, height: 6, borderRadius: 3 },
  dotNormal: { backgroundColor: '#1565C0' },
  dotHot: { backgroundColor: '#f44336' },
  legend: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendText: { fontSize: 12, color: '#666', marginRight: 12 },
  range: { fontSize: 12, color: '#888', marginTop: 4 },
});
