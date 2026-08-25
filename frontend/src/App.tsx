import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Preloader } from './components/Preloader';
import { HomePage } from './pages/HomePage';
import { ContactPage } from './pages/ContactPage';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { AssessmentPage } from './pages/AssessmentPage';
import { CandidateDetailPage } from './pages/CandidateDetailPage';

function App() {
  const [loading, setLoading] = useState(true);

  return (
    <Router>
      <AnimatePresence>
        {loading && <Preloader onComplete={() => setLoading(false)} />}
      </AnimatePresence>

      {!loading && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="min-h-screen bg-gray-50 dark:bg-page-gradient overflow-x-hidden relative transition-colors duration-500"
        >
          {/* Background ambient glows */}
          <div className="absolute top-[-10%] left-[-10%] w-[800px] h-[800px] bg-founder-primary/5 dark:bg-founder-primary/10 rounded-full blur-[150px] pointer-events-none"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[800px] h-[800px] bg-founder-secondary/5 rounded-full blur-[150px] pointer-events-none"></div>
          
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dashboard/:tabId" element={<DashboardPage />} />
            <Route path="/hiring" element={<DashboardPage />} />
            <Route path="/hiring/jobs/:jobId" element={<DashboardPage />} />
            <Route path="/hiring/candidates/:candidateId" element={<CandidateDetailPage />} />
            <Route path="/hiring/assessment/:assessmentId" element={<AssessmentPage />} />
          </Routes>
        </motion.div>
      )}
    </Router>
  );
}

export default App;
