import React, { useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { TouchableOpacity, Text } from 'react-native';

import InputScreen from './src/screens/InputScreen';
import ProcessingScreen from './src/screens/ProcessingScreen';
import ResultsScreen from './src/screens/ResultsScreen';
import { LangContext } from './src/i18n/useTranslation';

const Stack = createNativeStackNavigator();

const LANGUAGES = ['en', 'hi', 'ta', 'bn', 'te'];
const NEXT_LANG_LABELS = { en: 'हिं', hi: 'தமி', ta: 'বাং', bn: 'తె', te: 'EN' };

export default function App() {
  const [lang, setLang] = useState('en');

  const toggleLang = () => {
    setLang(current => {
      const idx = LANGUAGES.indexOf(current);
      return LANGUAGES[(idx + 1) % LANGUAGES.length];
    });
  };

  return (
    <LangContext.Provider value={{ lang, setLang }}>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Input"
          screenOptions={{
            headerStyle: { backgroundColor: '#1565C0' },
            headerTintColor: '#fff',
            headerTitleStyle: { fontWeight: '700' },
            headerRight: () => (
              <TouchableOpacity onPress={toggleLang} style={{ padding: 6 }}>
                <Text style={{ color: '#fff', fontWeight: '600' }}>
                  {NEXT_LANG_LABELS[lang] || 'EN'}
                </Text>
              </TouchableOpacity>
            ),
          }}
        >
          <Stack.Screen name="Input" component={InputScreen} options={{ title: '💉 ColdGuard' }} />
          <Stack.Screen name="Processing" component={ProcessingScreen} options={{ title: 'Analyzing…', headerBackVisible: false }} />
          <Stack.Screen name="Results" component={ResultsScreen} options={{ title: 'Result' }} />
        </Stack.Navigator>
      </NavigationContainer>
    </LangContext.Provider>
  );
}
