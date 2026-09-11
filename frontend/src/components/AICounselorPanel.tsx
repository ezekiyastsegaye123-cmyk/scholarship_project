import React, { useState } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  HelpCircle,
  AlertTriangle,
  RefreshCw,
  BookOpen,
} from 'lucide-react';
import { askAICounselor } from '../api/client';
import type { AICounselorResponse, ChatMessage, EpistemicStatus } from '../types';

interface AICounselorPanelProps {
  opportunityId: string;
  opportunityTitle?: string;
  isAuthenticated: boolean;
  onOpenAuthModal?: () => void;
}

export const AICounselorPanel: React.FC<AICounselorPanelProps> = ({
  opportunityId,
  opportunityTitle = 'this scholarship',
  isAuthenticated,
  onOpenAuthModal,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastResponse, setLastResponse] = useState<AICounselorResponse | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const quickPrompts = [
    'Why am I eligible for this scholarship?',
    'What requirements or criteria am I missing?',
    'Does this cover living expenses and room & board?',
    'What are my key deadlines and next steps?',
  ];

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || loading) return;

    if (!isAuthenticated) {
      if (onOpenAuthModal) onOpenAuthModal();
      return;
    }

    setErrorMessage(null);
    setLoading(true);

    const userTurn: ChatMessage = { role: 'user', content: query };
    const updatedMessages = [...messages, userTurn];
    setMessages(updatedMessages);
    setInputMessage('');

    try {
      const response = await askAICounselor(opportunityId, query, messages.slice(-6));
      setLastResponse(response);
      const assistantTurn: ChatMessage = { role: 'assistant', content: response.answer };
      setMessages([...updatedMessages, assistantTurn]);
    } catch (err: any) {
      let msg = 'Failed to get counselor advice. Please try again.';
      if (err.status === 429) {
        msg = 'Rate limit reached: Please wait a moment before asking another question.';
      } else if (err.status === 400 && err.data?.detail) {
        msg = err.data.detail;
      } else if (err.message) {
        msg = err.message;
      }
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  const getEpistemicBadge = (status: EpistemicStatus) => {
    switch (status) {
      case 'GROUNDED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            Fully Grounded in Official Facts
          </span>
        );
      case 'PARTIALLY_GROUNDED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-300">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            Partially Grounded
          </span>
        );
      case 'INSUFFICIENT_INFORMATION':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-300">
            <HelpCircle className="w-3.5 h-3.5 mr-1" />
            Information Pending Verification
          </span>
        );
      case 'CONFLICTING_INFORMATION':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-300">
            <AlertTriangle className="w-3.5 h-3.5 mr-1" />
            Conflicting Evidence Detected
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <section
      aria-label="AI Scholarship Counselor"
      className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
    >
      {/* Panel Header */}
      <div className="bg-gradient-to-r from-indigo-900 to-indigo-800 text-white p-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-700/60 rounded-lg">
              <Bot className="w-6 h-6 text-indigo-200" />
            </div>
            <div>
              <h2 className="text-lg font-bold flex items-center gap-2">
                AI Scholarship Counselor
                <Sparkles className="w-4 h-4 text-amber-300" />
              </h2>
              <p className="text-xs text-indigo-200">
                Evidence-grounded explanation of requirements, deadlines, and funding. Zero speculation.
              </p>
            </div>
          </div>
          {lastResponse && (
            <div className="flex items-center gap-2">
              {getEpistemicBadge(lastResponse.epistemic_status)}
              {lastResponse.is_fallback && (
                <span className="text-xs bg-amber-500/20 text-amber-200 border border-amber-400/40 px-2 py-0.5 rounded-md">
                  Fallback Engine
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Body */}
      <div className="p-5 space-y-5">
        {/* Unauthenticated notice */}
        {!isAuthenticated && (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
              <span>Sign in with your student account to receive personalized, grounded counselor explanations.</span>
            </div>
            {onOpenAuthModal && (
              <button
                type="button"
                onClick={onOpenAuthModal}
                className="ml-3 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
              >
                Sign In
              </button>
            )}
          </div>
        )}

        {/* Quick Suggestion Chips */}
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
            Suggested Questions for {opportunityTitle}
          </span>
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                disabled={loading || !isAuthenticated}
                onClick={() => handleSendMessage(prompt)}
                className="text-xs px-3 py-1.5 rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300 border border-slate-200 text-slate-700 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Conversation Thread */}
        <div className="border border-slate-100 bg-slate-50/60 rounded-lg p-4 min-h-[160px] max-h-[460px] overflow-y-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              <Bot className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="font-medium text-slate-600">No questions asked yet.</p>
              <p className="text-xs mt-1 max-w-md mx-auto text-slate-500">
                Click one of the suggested prompts above or type a specific inquiry to see verified eligibility alignment and transparent source evidence.
              </p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3.5 text-sm ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-sm'
                      : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 rounded-lg rounded-bl-none p-3.5 shadow-sm text-sm text-slate-500 flex items-center space-x-2">
                <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
                <span>Grounding facts against verified repository records...</span>
              </div>
            </div>
          )}
        </div>

        {/* Structured Evidence & Citations from Last Response */}
        {lastResponse && (
          <div className="space-y-4 pt-2 border-t border-slate-100">
            {/* Known Facts & Next Steps Tags */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {lastResponse.known_facts && lastResponse.known_facts.length > 0 && (
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-lg p-3">
                  <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Verified Established Facts
                  </h4>
                  <ul className="text-xs text-emerald-800 space-y-1">
                    {lastResponse.known_facts.map((fact, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-500 font-bold">•</span>
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {lastResponse.next_steps && lastResponse.next_steps.length > 0 && (
                <div className="bg-indigo-50/70 border border-indigo-200 rounded-lg p-3">
                  <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                    Recommended Next Steps
                  </h4>
                  <ul className="text-xs text-indigo-800 space-y-1">
                    {lastResponse.next_steps.map((step, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-indigo-500 font-bold">{i + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Citations List */}
            {lastResponse.sources && lastResponse.sources.length > 0 && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                  Official Source Citations & Provenance
                </h4>
                <div className="space-y-2">
                  {lastResponse.sources.map((src, i) => (
                    <div
                      key={i}
                      className="text-xs bg-white border border-slate-200 rounded p-2.5 flex flex-col gap-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-800">{src.title}</span>
                        {src.authority_tier && (
                          <span className="text-[10px] font-medium uppercase px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                            {src.authority_tier}
                          </span>
                        )}
                      </div>
                      {src.evidence_quote && (
                        <blockquote className="italic text-slate-600 border-l-2 border-indigo-400 pl-2 text-[11px] my-1">
                          "{src.evidence_quote}"
                        </blockquote>
                      )}
                      {src.url && (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-medium mt-0.5 text-[11px]"
                        >
                          Visit verified source <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Input Field and Action */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={loading || !isAuthenticated}
            placeholder={
              isAuthenticated
                ? "Ask a question about requirements, funding, or deadlines..."
                : "Sign in to ask questions..."
            }
            className="flex-1 px-4 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={loading || !inputMessage.trim() || !isAuthenticated}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <span>Ask</span>
            <Send className="w-4 h-4" />
          </button>
        </form>

        {/* Mandatory Epistemic Disclaimer */}
        <p className="text-[11px] text-slate-500 italic text-center border-t border-slate-100 pt-3">
          {lastResponse?.disclaimer ||
            'AI guidance explains verified scholarship facts from institutional records. It never calculates winning chances or guarantees admissions. Always verify details with official sources.'}
        </p>
      </div>
    </section>
  );
};
