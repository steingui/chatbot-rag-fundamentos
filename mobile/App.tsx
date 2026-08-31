import React, { useState, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  Linking,
} from 'react-native';
import { useMobileChatStore, Message } from './src/store/useMobileChatStore';
import { Send, Trash2, ShieldCheck, ExternalLink, Sparkles } from 'lucide-react-native';

const QUICK_SUGGESTIONS = [
  'Quais as últimas votações da Câmara?',
  'Resumo do orçamento da saúde 2026',
  'Verificar declaração de bens do TSE',
];

export default function App() {
  const [inputQuery, setInputQuery] = useState('');
  const { messages, isLoading, error, sendMessage, clearMessages } = useMobileChatStore();
  const flatListRef = useRef<FlatList>(null);

  const handleSend = () => {
    if (!inputQuery.trim() || isLoading) return;
    const query = inputQuery;
    setInputQuery('');
    sendMessage(query);
  };

  const handleSuggestionPress = (prompt: string) => {
    sendMessage(prompt);
  };

  const renderMessageItem = ({ item }: { item: Message }) => {
    const isUser = item.sender === 'user';
    return (
      <View
        style={[
          styles.messageRow,
          isUser ? styles.userRow : styles.botRow,
        ]}
      >
        <View
          style={[
            styles.messageBubble,
            isUser ? styles.userBubble : styles.botBubble,
          ]}
        >
          {!isUser && (
            <View style={styles.botBadgeContainer}>
              <Sparkles size={14} color="#60A5FA" />
              <Text style={styles.botBadgeText}>Assistente RAG</Text>
            </View>
          )}
          <Text style={isUser ? styles.userMessageText : styles.botMessageText}>
            {item.text}
          </Text>

          {item.sources && item.sources.length > 0 && (
            <View style={styles.sourcesContainer}>
              <Text style={styles.sourcesTitle}>Fontes Verificadas:</Text>
              <View style={styles.sourcesList}>
                {item.sources.map((src, idx) => (
                  <TouchableOpacity
                    key={idx}
                    style={styles.sourceChip}
                    onPress={() => src.url && Linking.openURL(src.url)}
                    disabled={!src.url}
                  >
                    <Text style={styles.sourceChipText}>{src.label}</Text>
                    {src.url && <ExternalLink size={12} color="#94A3B8" style={{ marginLeft: 4 }} />}
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          <Text style={styles.timestampText}>{item.timestamp}</Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0F172A" />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTitleContainer}>
          <ShieldCheck size={24} color="#38BDF8" />
          <View style={{ marginLeft: 10 }}>
            <Text style={styles.headerTitle}>RAG Político Mobile</Text>
            <Text style={styles.headerSubtitle}>Base Legislativa & Eleitoral</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.iconButton} onPress={clearMessages}>
          <Trash2 size={20} color="#94A3B8" />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Chat List */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessageItem}
          contentContainerStyle={styles.listContent}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        {error && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Quick Suggestions Bar */}
        {messages.length <= 2 && (
          <View style={styles.suggestionsContainer}>
            <Text style={styles.suggestionsHeader}>Sugestões rápidas:</Text>
            <FlatList
              horizontal
              showsHorizontalScrollIndicator={false}
              data={QUICK_SUGGESTIONS}
              keyExtractor={(item) => item}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.suggestionButton}
                  onPress={() => handleSuggestionPress(item)}
                >
                  <Text style={styles.suggestionText}>{item}</Text>
                </TouchableOpacity>
              )}
            />
          </View>
        )}

        {/* Input Bar */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Pergunte sobre leis, votações ou candidatos..."
            placeholderTextColor="#64748B"
            value={inputQuery}
            onChangeText={setInputQuery}
            multiline
          />
          <TouchableOpacity
            style={[styles.sendButton, (!inputQuery.trim() || isLoading) && styles.sendButtonDisabled]}
            onPress={handleSend}
            disabled={!inputQuery.trim() || isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Send size={18} color="#FFFFFF" />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
    backgroundColor: '#0F172A',
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F8FAFC',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#64748B',
  },
  iconButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#1E293B',
  },
  listContent: {
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  messageRow: {
    marginVertical: 6,
    flexDirection: 'row',
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  botRow: {
    justifyContent: 'flex-start',
  },
  messageBubble: {
    maxWidth: '85%',
    borderRadius: 16,
    padding: 14,
  },
  userBubble: {
    backgroundColor: '#2563EB',
    borderBottomRightRadius: 4,
  },
  botBubble: {
    backgroundColor: '#1E293B',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#334155',
  },
  botBadgeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  botBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#60A5FA',
    marginLeft: 4,
  },
  userMessageText: {
    fontSize: 15,
    color: '#FFFFFF',
    lineHeight: 22,
  },
  botMessageText: {
    fontSize: 15,
    color: '#E2E8F0',
    lineHeight: 22,
  },
  sourcesContainer: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  sourcesTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#94A3B8',
    marginBottom: 6,
  },
  sourcesList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  sourceChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0F172A',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#475569',
  },
  sourceChipText: {
    fontSize: 11,
    color: '#CBD5E1',
  },
  timestampText: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 6,
    alignSelf: 'flex-end',
  },
  suggestionsContainer: {
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  suggestionsHeader: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 6,
  },
  suggestionButton: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  suggestionText: {
    fontSize: 13,
    color: '#38BDF8',
  },
  errorBanner: {
    backgroundColor: '#7F1D1D',
    padding: 10,
    marginHorizontal: 14,
    borderRadius: 8,
    marginBottom: 8,
  },
  errorText: {
    color: '#FECACA',
    fontSize: 13,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
    backgroundColor: '#0F172A',
  },
  input: {
    flex: 1,
    backgroundColor: '#1E293B',
    color: '#F8FAFC',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2563EB',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#334155',
  },
});
