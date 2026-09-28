'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface RiskGaugeProps {
  score: number;
  verdict: 'SHIP' | 'CANARY' | 'HOLD';
  size?: number;
}

export function RiskGauge({ score, verdict, size = 180 }: RiskGaugeProps) {
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = Math.PI * radius;
  const clampedScore = Math.min(Math.max(score, 0), 100);
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  const getColor = () => {
    if (verdict === 'HOLD' || clampedScore >= 70) return '#FF4D6D';
    if (verdict === 'CANARY' || clampedScore >= 40) return '#FFB020';
    return '#2DD4A0';
  };

  const color = getColor();

  return (
    <div className="relative flex flex-col items-center justify-center select-none" style={{ width: size, height: size / 1.6 + 20 }}>
      <svg
        width={size}
        height={size / 2 + strokeWidth}
        viewBox={`0 0 ${size} ${size / 2 + strokeWidth}`}
        className="overflow-visible"
      >
        <defs>
          <filter id="gauge-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="glow" />
            <feComposite in="SourceGraphic" in2="glow" operator="over" />
          </filter>
        </defs>

        <path
          d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
          fill="none"
          stroke="#1F2430"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        <motion.path
          d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          filter="url(#gauge-glow)"
        />
      </svg>

      <div className="absolute top-[40%] flex flex-col items-center justify-center text-center">
        <motion.span
          className="text-4xl font-extrabold tracking-tight font-mono"
          style={{ color }}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          {score}
        </motion.span>
        <span className="text-xs font-semibold uppercase tracking-wider text-[#8A90A2] mt-0.5">
          Risk Score
        </span>
      </div>
    </div>
  );
}
