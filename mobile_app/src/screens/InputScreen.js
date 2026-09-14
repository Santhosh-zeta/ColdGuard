import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  TextInput, Alert, ActivityIndicator, Platform,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Picker } from '@react-native-picker/picker';
import { useTranslation } from '../i18n/useTranslation';
import {
  VACCINE_DB,
  monteCarloSamples,
  computePosteriorSummary,
  makeDecision
} from '../engine/arrhenius';

const VACCINES = Object.keys(VACCINE_DB);

export default function InputScreen({ navigation }) {
  const { t } = useTranslation();

  const [vaccine, setVaccine] = useState('DPT');
  const [rows, setRows] = useState([
    { time: '', temp: '' },
    { time: '', temp: '' },
  ]);
  const [computing, setComputing] = useState(false);

  const [loggerId, setLoggerId] = useState('');
  const [scannerVisible, setScannerVisible] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();

  const addRow = () => {
    setRows(r => [...r, { time: '', temp: '' }]);
  };

  function parseLoggerId(rawValue) {
    if (!rawValue) return null;

    const raw = rawValue.trim();

    // Try URL-encoded JSON
    try {
      const decoded = decodeURIComponent(raw);
      const data = JSON.parse(decoded);

      return (
        data.loggerId ||
        data.loggerID ||
        data.logger_id ||
        null
      );
    } catch {}

    // Try URL query parameters
    try {
      const url = new URL(raw);

      return (
        url.searchParams.get('loggerId') ||
        url.searchParams.get('loggerID') ||
        url.searchParams.get('logger_id') ||
        null
      );
    } catch {}

    return null;
  }

  const openScanner = async () => {
    if (!permission?.granted) {
      const result = await requestPermission();

      if (!result.granted) {
        Alert.alert(
          'Camera Permission',
          'Camera access is required to scan the logger. You can still enter the Logger ID manually.'
        );
        return;
      }
    }

    setScannerVisible(true);
  };

  const handleBarcodeScanned = ({ data }) => {
    const id = parseLoggerId(data);

    if (!id) {
      Alert.alert(
        'Invalid QR Code',
        'This QR code does not contain a recognizable Berlinger logger ID.'
      );
      return;
    }

    setLoggerId(id);
    setScannerVisible(false);
  };

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

    const timestamps = valid.map(
      r => new Date(r.time).getTime() / 1000
    );

    const temperatures = valid.map(
      r => parseFloat(r.temp)
    );

    if (timestamps.some(isNaN) || temperatures.some(isNaN)) {
      Alert.alert(t('error'), t('invalidData'));
      return;
    }

    setComputing(true);

    navigation.navigate('Processing', {
      vaccine,
      timestamps,
      temperatures,
    });

    setComputing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.title}>
        {t('inputTitle')}
      </Text>

      {/* Logger ID */}
      <Text style={styles.label}>
        Logger ID
      </Text>

      <View style={styles.loggerRow}>
        <TextInput
          style={[styles.input, styles.loggerInput]}
          placeholder="Enter Logger ID"
          value={loggerId}
          onChangeText={setLoggerId}
          autoCapitalize="none"
        />

        <TouchableOpacity
          style={styles.scanBtn}
          onPress={openScanner}
        >
          <Text style={styles.scanBtnText}>
            Scan Logger
          </Text>
        </TouchableOpacity>
      </View>

      {/* QR Scanner */}
      {scannerVisible && (
        <View style={styles.scannerContainer}>
          <CameraView
            style={styles.camera}
            facing="back"
            barcodeScannerSettings={{
              barcodeTypes: ['qr', 'dataMatrix'],
            }}
            onBarcodeScanned={handleBarcodeScanned}
          />

          <TouchableOpacity
            style={styles.closeScannerBtn}
            onPress={() => setScannerVisible(false)}
          >
            <Text style={styles.closeScannerText}>
              Cancel
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Vaccine */}
      <Text style={styles.label}>
        {t('vaccineType')}
      </Text>

      <View style={styles.pickerWrapper}>
        <Picker
          selectedValue={vaccine}
          onValueChange={setVaccine}
          style={styles.picker}
        >
          {VACCINES.map(v => (
            <Picker.Item
              key={v}
              label={t('vaccines')?.[v] || VACCINE_DB[v].name}
              value={v}
            />
          ))}
        </Picker>
      </View>

      {/* Temperature Log */}
      <Text style={styles.label}>
        {t('temperatureLog')}
      </Text>

      <Text style={styles.hint}>
        {t('formatHint')}
      </Text>

      {rows.map((row, idx) => (
        <View key={idx} style={styles.row}>
          <TextInput
            style={[styles.input, styles.inputWide]}
            placeholder="2024-09-01T08:00:00"
            value={row.time}
            onChangeText={v =>
              updateRow(idx, 'time', v)
            }
          />

          <TextInput
            style={[styles.input, styles.inputNarrow]}
            placeholder="°C"
            value={row.temp}
            keyboardType="decimal-pad"
            onChangeText={v =>
              updateRow(idx, 'temp', v)
            }
          />
        </View>
      ))}

      <TouchableOpacity
        style={styles.addBtn}
        onPress={addRow}
      >
        <Text style={styles.addBtnText}>
          {t('addRow')}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[
          styles.analyzeBtn,
          computing && styles.disabled
        ]}
        onPress={analyze}
        disabled={computing}
      >
        {computing
          ? <ActivityIndicator color="#fff" />
          : (
            <Text style={styles.analyzeBtnText}>
              {t('analyze')}
            </Text>
          )
        }
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f4f8',
    padding: 16,
  },

  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1565C0',
    marginBottom: 16,
  },

  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
    marginTop: 12,
  },

  hint: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },

  pickerWrapper: {
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    marginBottom: 4,
  },

  picker: {
    height: 50,
  },

  row: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 6,
  },

  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 10,
    fontSize: 13,
  },

  inputWide: {
    flex: 3,
  },

  inputNarrow: {
    flex: 1,
  },

  loggerRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },

  loggerInput: {
    flex: 1,
  },

  scanBtn: {
    backgroundColor: '#2E7D32',
    borderRadius: 8,
    paddingHorizontal: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },

  scanBtnText: {
    color: '#fff',
    fontWeight: '700',
  },

  scannerContainer: {
    height: 400,
    marginTop: 8,
    marginBottom: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },

  camera: {
    flex: 1,
  },

  closeScannerBtn: {
    backgroundColor: '#333',
    padding: 12,
    alignItems: 'center',
  },

  closeScannerText: {
    color: '#fff',
    fontWeight: '700',
  },

  addBtn: {
    padding: 10,
    alignItems: 'center',
    marginTop: 4,
  },

  addBtnText: {
    color: '#1565C0',
    fontWeight: '600',
  },

  analyzeBtn: {
    backgroundColor: '#1565C0',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 32,
  },

  analyzeBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },

  disabled: {
    opacity: 0.6,
  },
});
