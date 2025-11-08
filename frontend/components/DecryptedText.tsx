'use client';

import { useEffect, useRef, useState } from 'react';
import './DecryptedText.css';

interface DecryptedTextProps {
  text: string;
  speed?: number;
  maxIterations?: number;
  characters?: string;
  className?: string;
  parentClassName?: string;
  encryptedClassName?: string;
  animateOn?: 'view' | 'hover';
  revealDirection?: 'start' | 'end' | 'center';
  sequential?: boolean;
}

const DecryptedText = ({
  text,
  speed = 50,
  maxIterations = 10,
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{}|;:,.<>?',
  className = '',
  parentClassName = '',
  encryptedClassName = '',
  animateOn = 'hover',
  revealDirection = 'start',
  sequential = false
}: DecryptedTextProps) => {
  const [displayText, setDisplayText] = useState(text);
  const [isAnimating, setIsAnimating] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const hasAnimatedRef = useRef(false);

  const getRandomChar = () => {
    return characters[Math.floor(Math.random() * characters.length)];
  };

  const animate = () => {
    if (isAnimating) return;

    setIsAnimating(true);
    let iteration = 0;
    const textLength = text.length;

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(() => {
      setDisplayText((prevText) => {
        return text
          .split('')
          .map((char, index) => {
            if (char === ' ') return ' ';

            let shouldReveal = false;

            if (revealDirection === 'start') {
              shouldReveal = index < iteration;
            } else if (revealDirection === 'end') {
              shouldReveal = index >= textLength - iteration;
            } else if (revealDirection === 'center') {
              const center = Math.floor(textLength / 2);
              const distance = Math.abs(index - center);
              shouldReveal = distance < iteration / 2;
            }

            if (shouldReveal) {
              return text[index];
            }

            return getRandomChar();
          })
          .join('');
      });

      iteration += sequential ? 0.5 : 1;

      if (iteration >= textLength + maxIterations) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
        setDisplayText(text);
        setIsAnimating(false);
      }
    }, speed);
  };

  useEffect(() => {
    if (animateOn === 'view') {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && !hasAnimatedRef.current) {
              hasAnimatedRef.current = true;
              animate();
            }
          });
        },
        { threshold: 0.1 }
      );

      if (containerRef.current) {
        observer.observe(containerRef.current);
      }

      return () => {
        if (containerRef.current) {
          observer.unobserve(containerRef.current);
        }
      };
    }
  }, [animateOn]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const handleMouseEnter = () => {
    if (animateOn === 'hover') {
      animate();
    }
  };

  return (
    <div
      ref={containerRef}
      className={`decrypted-text-container ${parentClassName}`}
      onMouseEnter={handleMouseEnter}
    >
      <span className={`decrypted-text ${className} ${isAnimating ? encryptedClassName : ''}`}>
        {displayText}
      </span>
    </div>
  );
};

export default DecryptedText;
