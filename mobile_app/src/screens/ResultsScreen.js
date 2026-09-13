import React from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
} from 'react-native';
import DecisionBanner from '../components/DecisionBanner';
import PotencyChart from '../components/PotencyChart';
import TemperatureTimeline from '../components/TemperatureTimeline';
import { useTranslation } from '../i18n/useTranslation';
import { VACCINE_DB } from '../engine/arrhenius';

export default function ResultsScreen({ route, navigation }) {
  const { vaccine, timestamps, temperatures, posterior, decision } = route.params;
  const { t } = useTranslation();
  const params = VACCINE_DB[vaccine];

  return (
    <ScrollView style={styles.container}>
      <DecisionBanner decision={decision} posterior={posterior} vaccineName={params.name} />

      <View style={styles.card}>
        <Text style={styles.cardTitle}>{t('potencyEstimate')}</Text>
        <PotencyChart posterior={posterior} threshold={params.minPotencyThreshold} />
        <Text style={styles.explanation}>{decision.explanation}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>{t('temperatureHistory')}</Text>
        <TemperatureTimeline timestamps={timestamps} temperatures={temperatures} />
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>{t('details')}</Text>
        <DetailRow label={t('mean')} value={`${(posterior.mean * 100).toFixed(1)}%`} />
        <DetailRow label={t('ci90')} value={`${(posterior.ci90Lower * 100).toFixed(1)}% – ${(posterior.ci90Upper * 100).toFixed(1)}%`} />
        <DetailRow label={t('probAboveThreshold')} value={`${(posterior.probAbove80 * 100).toFixed(0)}%`} />
        <DetailRow label={t('confidence')} value={`${(decision.confidence * 100).toFixed(0)}%`} />
      </View>

      <TouchableOpacity
        style={styles.retryBtn}
        onPress={() => navigation.navigate('Input')}
      >
        <Text style={styles.retryBtnText}>{t('analyzeAnother')}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function DetailRow({ label, value }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f4f8' },
  card: { backgroundColor: '#fff', margin: 12, marginTop: 0, borderRadius: 12, padding: 16, elevation: 2 },
  cardTitle: { fontSize: 16, fontWeight: '700', color: '#333', marginBottom: 12 },
  explanation: { fontSize: 14, color: '#444', lineHeight: 20, marginTop: 12 },
  detailRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  detailLabel: { fontSize: 14, color: '#666' },
  detailValue: { fontSize: 14, fontWeight: '600', color: '#333' },
  retryBtn: { margin: 16, backgroundColor: '#1565C0', borderRadius: 10, padding: 14, alignItems: 'center', marginBottom: 32 },
  retryBtnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
});
