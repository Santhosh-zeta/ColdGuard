import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  TextInput, Alert, ActivityIndicator, Platform,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { useTranslation } from '../i18n/useTranslation';
import { VACCINE_DB, monteCarloSamples, computePosteriorSummary, makeDecision } from '../engine/arrhenius';

const VACCINES = Object.keys(VACCINE_DB);

export default function InputScreen({ navigation }) {
  const { t } = useTranslation();
  const [vaccine, setVaccine] = useState('DPT');
  const [rows, setRows] = useState([
    { time: '', temp: '' },
    { time: '', temp: '' },
  ]);
  const [computing, setComputing] = useState(false);

  const addRow = () => setRows(r => [...r, { time: '', temp: '' }]);

  const updateRow = (idx, field, value) => {
    setRows(prev => {
      const next = [...prev];
      next[idx] = { ...next[idx], [field]: value };
      return next;
    });
  };

  const analyze = async () => {
    const valid = rows.filter(r => r.time.trim() && r.temp.trim());
    if (valid.length < 2) {
      Alert.alert(t('error'), t('needTwoReadings'));
      return;
    }
    const timestamps = valid.map(r => new Date(r.time).getTime() / 1000);
    const temperatures = valid.map(r => parseFloat(r.temp));
    if (timestamps.some(isNaN) || temperatures.some(isNaN)) {
      Alert.alert(t('error'), t('invalidData'));
      return;
    }
    setComputing(true);
    navigation.navigate('Processing', {
      vaccine, timestamps, temperatures,
    });
    setComputing(false);
  };

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>{t('inputTitle')}</Text>

      <Text style={styles.label}>{t('vaccineType')}</Text>
      <View style={styles.pickerWrapper}>
        <Picker selectedValue={vaccine} onValueChange={setVaccine} style={styles.picker}>
          {VACCINES.map(v => (
            <Picker.Item key={v} label={VACCINE_DB[v].name} value={v} />
          ))}
        </Picker>
      </View>

      <Text style={styles.label}>{t('temperatureLog')}</Text>
      <Text style={styles.hint}>{t('formatHint')}</Text>

      {rows.map((row, idx) => (
        <View key={idx} style={styles.row}>
          <TextInput
            style={[styles.input, styles.inputWide]}
            placeholder="2024-09-01T08:00:00"
            value={row.time}
            onChangeText={v => updateRow(idx, 'time', v)}
          />
          <TextInput
            style={[styles.input, styles.inputNarrow]}
            placeholder="°C"
            value={row.temp}
            keyboardType="decimal-pad"
            onChangeText={v => updateRow(idx, 'temp', v)}
          />
        </View>
      ))}

      <TouchableOpacity style={styles.addBtn} onPress={addRow}>
        <Text style={styles.addBtnText}>{t('addRow')}</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.analyzeBtn, computing && styles.disabled]}
        onPress={analyze}
        disabled={computing}
      >
        {computing
          ? <ActivityIndicator color="#fff" />
          : <Text style={styles.analyzeBtnText}>{t('analyze')}</Text>
        }
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f4f8', padding: 16 },
  title: { fontSize: 20, fontWeight: '700', color: '#1565C0', marginBottom: 16 },
  label: { fontSize: 14, fontWeight: '600', color: '#333', marginBottom: 4, marginTop: 12 },
  hint: { fontSize: 12, color: '#666', marginBottom: 8 },
  pickerWrapper: { backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#ddd', marginBottom: 4 },
  picker: { height: 50 },
  row: { flexDirection: 'row', gap: 8, marginBottom: 6 },
  input: { backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#ddd', padding: 10, fontSize: 13 },
  inputWide: { flex: 3 },
  inputNarrow: { flex: 1 },
  addBtn: { padding: 10, alignItems: 'center', marginTop: 4 },
  addBtnText: { color: '#1565C0', fontWeight: '600' },
  analyzeBtn: { backgroundColor: '#1565C0', borderRadius: 10, padding: 16, alignItems: 'center', marginTop: 16, marginBottom: 32 },
  analyzeBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  disabled: { opacity: 0.6 },
});
