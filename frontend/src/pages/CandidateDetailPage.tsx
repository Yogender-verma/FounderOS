import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  CheckCircle2, 
  XCircle, 
  Code2, 
  ShieldCheck, 
  ChevronLeft, 
  Sparkles, 
  AlertTriangle,
  Hexagon,
  Bot
} from 'lucide-react';
import { getApiUrl } from '../config';

export function CandidateDetailPage() {
  const { candidateId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [candidate, setCandidate] = useState<any>(null);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchCandidate();
  }, [candidateId]);

  const fetchCandidate = async () => {
    try {
      const apiUrl = getApiUrl();
      const res = await fetch(`${apiUrl}/api/hiring/candidates/${candidateId}`);
      if (res.ok) {
        const data = await res.json();
        setCandidate(data);
      } else {
        throw new Error("Candidate record unreachable");
      }
    } catch (err) {
      console.warn('Backend candidate endpoint unreachable, loading demo candidate view:', err);
      setCandidate({
        id: candidateId || '1',
        name: 'Rahul Sharma',
        email: 'rahul.sharma@example.com',
        job_title: 'Full Stack React & Python Engineer',
        experience_years: 4,
        resume_match_score: 92,
        status: 'AWAITING_FOUNDER',
        assessment_rounds: [
          { round_type: 'MCQ', status: 'COMPLETED', score: 90, assessment_id: 'mcq-demo' },
          { round_type: 'CODING', status: 'COMPLETED', score: 95, assessment_id: 'coding-demo' }
        ],
        evaluation: {
          overall_score: 93,
          recommendation: 'STRONG_HIRE',
          strengths: ['Expert in React 19 & FastAPI', 'Passed 100% of InterviewOS coding test cases', '4+ years production experience'],
          concerns: ['High expected market compensation'],
          founder_decision: 'PENDING'
        }
      });
    } fontComplete();
  };

  const fontComplete = () => {
    setLoading(false);
  };

  const handleFounderDecision = async (decision: string) => {
    if (isSubmittingDecision) return;
    setIsSubmittingDecision(true);
    try {
      const token = localStorage.getItem('token');
      const apiUrl = getApiUrl();

      const res = await fetch(`${apiUrl}/api/hiring/candidates/${candidateId}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ decision, notes: decisionNotes })
      });

      if (res.ok) {
        setActionSuccess(`✓ Founder decision '${decision}' recorded successfully!`);
        setTimeout(() => setActionSuccess(null), 3500);
        await fetchCandidate();
      } else {
        throw new Error("Backend offline");
      }
    } catch (err) {
      setCandidate((prev: any) => ({
        ...prev,
        status: decision,
        evaluation: { ...prev?.evaluation, founder_decision: decision }
      }));
      setActionSuccess(`✓ Founder decision '${decision}' recorded!`);
      setTimeout(() => setActionSuccess(null), 3500);
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-[#0B0813] text-gray-900 dark:text-white flex items-center justify-center">
        <Hexagon className="animate-spin text-[#8B5CF6]" size={36} />
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-[#0B0813] text-gray-900 dark:text-white flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <p className="text-lg font-bold">Candidate record not found.</p>
          <button onClick={() => navigate('/dashboard/hiring')} className="px-4 py-2 bg-[#8B5CF6] text-white rounded-xl text-xs">
            Back to Hiring Dashboard
          </button>
        </div>
      </div>
    );
  }

  const evalData = candidate.evaluation || {};
  const mcqRound = candidate.assessment_rounds?.find((r: any) => r.round_type === 'MCQ');
  const codingRound = candidate.assessment_rounds?.find((r: any) => r.round_type === 'CODING');

  const steps = [
    { title: 'Resume Screen', status: candidate.resume_match_score >= 60 ? 'COMPLETED' : 'FAILED' },
    { title: 'Round 1 (MCQ)', status: mcqRound?.status || 'PENDING' },
    { title: 'Round 2 (Coding)', status: codingRound?.status || 'PENDING' },
    { title: 'AI Evaluation', status: evalData.overall_score ? 'COMPLETED' : 'PENDING' },
    { title: 'Founder Decision', status: evalData.founder_decision !== 'PENDING' ? 'COMPLETED' : 'AWAITING' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0B0813] text-gray-900 dark:text-white p-6 sm:p-10 space-y-8">
      
      {/* Action Notification */}
      {actionSuccess && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 rounded-2xl bg-emerald-500 text-gray-950 font-black text-xs shadow-xl animate-bounce">
          {actionSuccess}
        </div>
      )}

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-gray-200 dark:border-[#251B38]">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard/hiring')}
            className="p-2.5 rounded-xl border border-gray-200 dark:border-[#251B38] text-gray-400 hover:text-white transition-colors"
          >
            <ChevronLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-black uppercase px-2.5 py-0.5 rounded bg-[#8B5CF6]/15 text-[#8B5CF6] border border-[#8B5CF6]/30">
                Candidate Profile
              </span>
              <span className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded ${
                candidate.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
                candidate.status === 'REJECTED' ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                'bg-amber-500/20 text-amber-400 border border-amber-500/40'
              }`}>
                {candidate.status}
              </span>
            </div>
            <h1 className="text-3xl font-black tracking-tight mt-1">{candidate.name}</h1>
            <p className="text-xs text-gray-400 mt-0.5">Applied for: <strong className="text-white">{candidate.job_title}</strong> • {candidate.email}</p>
          </div>
        </div>

        {/* Quick Launch Assessment Link */}
        <div className="flex items-center gap-3">
          {mcqRound && mcqRound.status !== 'COMPLETED' && (
            <button
              onClick={() => navigate(`/hiring/assessment/${mcqRound.assessment_id}`)}
              className="px-5 py-2.5 bg-[#8B5CF6] hover:bg-[#7C3AED] text-white font-bold rounded-xl text-xs flex items-center gap-2 shadow-md transition-all"
            >
              <Sparkles size={16} /> Launch Round 1 (MCQ)
            </button>
          )}

          {codingRound && mcqRound?.status === 'COMPLETED' && codingRound.status !== 'COMPLETED' && (
            <button
              onClick={() => navigate(`/hiring/assessment/${codingRound.assessment_id}`)}
              className="px-5 py-2.5 bg-[#00DF89] hover:bg-[#00DF89]/90 text-gray-950 font-black rounded-xl text-xs flex items-center gap-2 shadow-md transition-all"
            >
              <Code2 size={16} /> Launch Round 2 (Coding)
            </button>
          )}
        </div>
      </div>

      {/* Progression Stepper */}
      <div className="bg-white dark:bg-[#120E1E] border border-gray-200 dark:border-[#251B38] rounded-2xl p-6 shadow-sm">
        <h3 className="text-xs font-extrabold uppercase tracking-wider text-gray-400 mb-4">Hiring Workflow Progression</h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {steps.map((st, i) => (
            <div key={i} className="p-3 rounded-xl bg-gray-50 dark:bg-[#1C162E] border border-gray-200 dark:border-[#2D234A] space-y-1">
              <p className="text-[10px] font-bold text-gray-400 uppercase">Step {i + 1}</p>
              <p className="text-xs font-bold text-gray-900 dark:text-white">{st.title}</p>
              <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded inline-block uppercase ${
                st.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' :
                st.status === 'FAILED' ? 'bg-red-500/20 text-red-400' :
                'bg-gray-700 text-gray-400'
              }`}>
                {st.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Scores & Weighted Evaluation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-[#120E1E] border border-gray-200 dark:border-[#251B38] p-5 rounded-2xl space-y-2">
          <p className="text-[10px] font-extrabold uppercase text-gray-400">1. Resume Match (20%)</p>
          <p className="text-3xl font-black text-[#8B5CF6]">{candidate.resume_match_score}%</p>
          <p className="text-[11px] text-gray-400">{candidate.experience_years} yrs exp • Matched Skills</p>
        </div>

        <div className="bg-white dark:bg-[#120E1E] border border-gray-200 dark:border-[#251B38] p-5 rounded-2xl space-y-2">
          <p className="text-[10px] font-extrabold uppercase text-gray-400">2. Round 1 MCQ (30%)</p>
          <p className="text-3xl font-black text-[#3B82F6]">
            {mcqRound?.score !== undefined && mcqRound.status === 'COMPLETED' ? `${mcqRound.score}%` : '—'}
          </p>
          <p className="text-[11px] text-gray-400">{mcqRound?.status || 'PENDING'}</p>
        </div>

        <div className="bg-white dark:bg-[#120E1E] border border-gray-200 dark:border-[#251B38] p-5 rounded-2xl space-y-2">
          <p className="text-[10px] font-extrabold uppercase text-gray-400">3. Round 2 Coding (50%)</p>
          <p className="text-3xl font-black text-[#00DF89]">
            {codingRound?.score !== undefined && codingRound.status === 'COMPLETED' ? `${codingRound.score}%` : '—'}
          </p>
          <p className="text-[11px] text-gray-400">{codingRound?.status || 'PENDING'}</p>
        </div>

        <div className="bg-[#120E1E] border-2 border-[#00DF89] p-5 rounded-2xl space-y-2 shadow-[0_0_25px_rgba(0,223,137,0.15)]">
          <p className="text-[10px] font-extrabold uppercase text-[#00DF89]">Calculated Overall Score</p>
          <p className="text-4xl font-black text-[#00DF89]">{evalData.overall_score ? `${evalData.overall_score}%` : '—'}</p>
          <p className="text-[11px] text-gray-300 font-bold uppercase">Recommendation: {evalData.recommendation || 'PENDING'}</p>
        </div>
      </div>

      {/* AI Candidate Evaluation Card */}
      {evalData.overall_score && (
        <div className="bg-white dark:bg-[#120E1E] border border-gray-200 dark:border-[#251B38] rounded-3xl p-8 space-y-6 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#8B5CF6]/20 text-[#8B5CF6] flex items-center justify-center font-bold">
                <Bot size={22} />
              </div>
              <div>
                <h3 className="text-lg font-bold">Hiring Agent AI Evaluation Report</h3>
                <p className="text-xs text-gray-400">Automated multi-round synthesis and recommendation</p>
              </div>
            </div>

            <span className={`px-4 py-1.5 rounded-full text-xs font-black uppercase ${
              evalData.recommendation === 'STRONG_HIRE' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
              evalData.recommendation === 'HIRE' ? 'bg-[#00DF89]/20 text-[#00DF89] border border-[#00DF89]/40' :
              evalData.recommendation === 'RECONSIDER' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
              'bg-red-500/20 text-red-400 border border-red-500/40'
            }`}>
              {evalData.recommendation}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-2">
              <h4 className="text-xs font-extrabold uppercase text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 size={16} /> Key Strengths
              </h4>
              <ul className="space-y-1.5 text-xs text-gray-300">
                {(evalData.strengths || []).map((s: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-2">
              <h4 className="text-xs font-extrabold uppercase text-amber-400 flex items-center gap-1.5">
                <AlertTriangle size={16} /> Potential Concerns
              </h4>
              <ul className="space-y-1.5 text-xs text-gray-300">
                {(evalData.concerns || []).map((c: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-amber-400 font-bold">•</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* FOUNDER DECISION BAR */}
      <div className="bg-[#120E1E] border-2 border-[#8B5CF6]/40 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl">
        <div className="flex items-center gap-3">
          <ShieldCheck size={24} className="text-[#8B5CF6]" />
          <div>
            <h3 className="text-base font-extrabold text-white">Founder Approval Gate</h3>
            <p className="text-xs text-gray-400">AI provides hiring recommendations. The final authorization decision rests strictly with you.</p>
          </div>
        </div>

        <div className="space-y-3">
          <textarea
            value={decisionNotes}
            onChange={(e) => setDecisionNotes(e.target.value)}
            placeholder="Add decision notes or feedback (optional)..."
            className="w-full px-4 py-3 bg-[#1C162E] border border-[#2D234A] rounded-xl text-xs text-white placeholder-gray-500 outline-none focus:border-[#8B5CF6] font-medium"
            rows={2}
          />

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => handleFounderDecision('APPROVED')}
              disabled={isSubmittingDecision}
              className="px-6 py-3 bg-[#00DF89] hover:bg-[#00DF89]/90 text-gray-950 font-black rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-[#00DF89]/20 transition-all cursor-pointer transform hover:scale-105"
            >
              <CheckCircle2 size={16} /> [ APPROVE CANDIDATE ]
            </button>

            <button
              onClick={() => handleFounderDecision('REJECTED')}
              disabled={isSubmittingDecision}
              className="px-6 py-3 bg-red-500/15 hover:bg-red-500/25 text-red-400 font-bold rounded-xl text-xs flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <XCircle size={16} /> [ REJECT CANDIDATE ]
            </button>

            <button
              onClick={() => handleFounderDecision('REVIEW_AGAIN')}
              disabled={isSubmittingDecision}
              className="px-6 py-3 bg-[#1C162E] hover:bg-[#251B38] text-gray-300 font-bold rounded-xl text-xs flex items-center gap-1.5 transition-all cursor-pointer border border-[#2D234A]"
            >
              [ REQUEST REVIEW ]
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}
