import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { monteCarloSamples, computePosteriorSummary, makeDecision } from '../engine/arrhenius';
import { useTranslation } from '../i18n/useTranslation';

export default function ProcessingScreen({ route, navigation }) {
  const { vaccine, timestamps, temperatures } = route.params;
  const { t } = useTranslation();

  useEffect(() => {
    // Run in a microtask so the UI renders the spinner first
    const timer = setTimeout(() => {
      try {
        const samples = monteCarloSamples(timestamps, temperatures, vaccine, 1000);
        const posterior = computePosteriorSummary(samples);
        const decision = makeDecision(posterior, vaccine);
        navigation.replace('Results', { vaccine, timestamps, temperatures, posterior, decision, samples });
      } catch (e) {
        navigation.goBack();
      }
    }, 50);
    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#1565C0" style={styles.spinner} />
      <Text style={styles.title}>{t('analyzing')}</Text>
      <Text style={styles.subtitle}>{t('runningMonteCarlo')}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f4f8' },
  spinner: { marginBottom: 24 },
  title: { fontSize: 20, fontWeight: '700', color: '#1565C0', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#555' },
});
