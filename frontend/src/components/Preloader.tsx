import { useEffect } from 'react';
import { motion } from 'framer-motion';

export function Preloader({ onComplete }: { onComplete: () => void }) {
  useEffect(() => {
    // Safety fallback to guarantee preloader dismisses and never blocks clicks
    const timer = setTimeout(() => {
      onComplete();
    }, 1000);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <motion.div 
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.4, ease: "easeInOut" } }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-gray-50 dark:bg-founder-darkest pointer-events-none"
    >
      {/* Background radial glow */}
      <motion.div 
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 0.5, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="absolute w-[400px] h-[400px] bg-founder-primary/20 rounded-full blur-[100px]"
      />

      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: [0.8, 1, 1, 30], opacity: [0, 1, 1, 0] }}
        transition={{ duration: 1.0, times: [0, 0.4, 0.7, 1], ease: "easeInOut" }}
        onAnimationComplete={onComplete}
        className="relative flex items-center justify-center z-10"
      >
        <svg viewBox="0 0 100 100" className="w-32 h-32 drop-shadow-[0_0_20px_rgba(136,51,255,0.8)]">
          <defs>
            <linearGradient id="glow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#8833FF" />
              <stop offset="100%" stopColor="#3388FF" />
            </linearGradient>
          </defs>
          <motion.path
            d="M50 5 C50 35 65 50 95 50 C65 50 50 65 50 95 C50 65 35 50 5 50 C35 50 50 35 50 5 Z"
            fill="none"
            stroke="url(#glow)"
            strokeWidth="3"
            initial={{ pathLength: 0, fill: "rgba(136, 51, 255, 0)" }}
            animate={{ pathLength: 1, fill: "rgba(136, 51, 255, 0.3)" }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
          />
          {/* Inner spark */}
          <motion.path
            d="M50 25 C50 40 60 50 75 50 C60 50 50 60 50 75 C50 60 40 50 25 50 C40 50 50 40 50 25 Z"
            fill="url(#glow)"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 0.8 }}
            transition={{ delay: 0.25, duration: 0.25, ease: "backOut" }}
            style={{ transformOrigin: "center" }}
          />
        </svg>
      </motion.div>
    </motion.div>
  );
}
