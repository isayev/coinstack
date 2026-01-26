/**
 * MarkdownContent - Styled markdown renderer for LLM-generated content
 * 
 * Renders markdown sections with proper styling for numismatic analysis:
 * - Section headers (## SECTION_NAME)
 * - Bold text (**text**)
 * - Italic text (*text*)
 * - Bullet points (- item)
 * - Inline references (RIC, RSC, etc.)
 */

import { useMemo } from 'react';
import { cn } from '@/lib/utils';

interface MarkdownContentProps {
  /** Raw markdown content */
  content: string;
  /** Additional CSS classes */
  className?: string;
}

// Section title mappings for prettier display
const SECTION_TITLES: Record<string, string> = {
  'EPIGRAPHY_AND_TITLES': 'Epigraphy & Titles',
  'ICONOGRAPHY_AND_SYMBOLISM': 'Iconography & Symbolism',
  'ARTISTIC_STYLE': 'Artistic Style & Portraiture',
  'PROPAGANDA_AND_MESSAGING': 'Propaganda & Political Messaging',
  'ECONOMIC_CONTEXT': 'Economic & Monetary Context',
  'DIE_STUDIES_AND_VARIETIES': 'Die Studies & Varieties',
  'ARCHAEOLOGICAL_CONTEXT': 'Archaeological & Provenance',
  'TYPOLOGICAL_RELATIONSHIPS': 'Typological Relationships',
  'MILITARY_HISTORY': 'Military History',
  'HISTORICAL_CONTEXT': 'Historical Context',
  'NUMISMATIC_SIGNIFICANCE': 'Numismatic Significance',
};

// Parse markdown into structured sections
function parseMarkdown(content: string): { title: string; items: string[] }[] {
  const sections: { title: string; items: string[] }[] = [];
  let currentSection: { title: string; items: string[] } | null = null;
  
  const lines = content.split('\n');
  
  for (const line of lines) {
    const trimmed = line.trim();
    
    // Section header (## SECTION_NAME)
    if (trimmed.startsWith('## ')) {
      if (currentSection && currentSection.items.length > 0) {
        sections.push(currentSection);
      }
      const rawTitle = trimmed.slice(3).trim();
      // Convert to prettier title
      const prettyTitle = SECTION_TITLES[rawTitle] || rawTitle.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      currentSection = { title: prettyTitle, items: [] };
    }
    // Bullet point
    else if (trimmed.startsWith('- ') && currentSection) {
      currentSection.items.push(trimmed.slice(2));
    }
    // Regular text line (part of current section)
    else if (trimmed && currentSection && !trimmed.startsWith('*Section omitted')) {
      // If it's a continuation or standalone text, add it
      if (currentSection.items.length > 0) {
        // Append to last item if it looks like continuation
        const lastIdx = currentSection.items.length - 1;
        currentSection.items[lastIdx] += ' ' + trimmed;
      } else {
        currentSection.items.push(trimmed);
      }
    }
    // Section omitted note - add as info
    else if (trimmed.startsWith('*Section omitted') && currentSection) {
      currentSection.items.push(trimmed);
    }
  }
  
  // Don't forget the last section
  if (currentSection && currentSection.items.length > 0) {
    sections.push(currentSection);
  }
  
  return sections;
}

// Render inline markdown (bold, italic)
function renderInlineMarkdown(text: string): React.ReactNode {
  // Split by bold (**text**) and italic (*text*)
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;
  
  while (remaining) {
    // Find bold first
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
    // Find italic (single asterisk, not part of bold)
    const italicMatch = remaining.match(/(?<!\*)\*([^*]+)\*(?!\*)/);
    
    if (boldMatch && boldMatch.index !== undefined && 
        (!italicMatch || italicMatch.index === undefined || boldMatch.index <= italicMatch.index)) {
      // Add text before bold
      if (boldMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.slice(0, boldMatch.index)}</span>);
      }
      // Add bold text
      parts.push(
        <strong 
          key={key++} 
          style={{ color: 'var(--text-primary)', fontWeight: 600 }}
        >
          {boldMatch[1]}
        </strong>
      );
      remaining = remaining.slice(boldMatch.index + boldMatch[0].length);
    } else if (italicMatch && italicMatch.index !== undefined) {
      // Add text before italic
      if (italicMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.slice(0, italicMatch.index)}</span>);
      }
      // Add italic text
      parts.push(
        <em 
          key={key++} 
          style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}
        >
          {italicMatch[1]}
        </em>
      );
      remaining = remaining.slice(italicMatch.index + italicMatch[0].length);
    } else {
      // No more matches
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }
  }
  
  return <>{parts}</>;
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  const sections = useMemo(() => parseMarkdown(content), [content]);
  
  if (sections.length === 0) {
    // Fallback to raw text if no sections found
    return (
      <p
        className={cn("text-sm leading-relaxed whitespace-pre-wrap", className)}
        style={{ color: 'var(--text-secondary)' }}
      >
        {content}
      </p>
    );
  }
  
  return (
    <div className={cn("space-y-6", className)}>
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-2">
          {/* Section Header */}
          <h3 
            className="text-sm font-semibold uppercase tracking-wide flex items-center gap-2"
            style={{ color: 'var(--text-primary)' }}
          >
            <span 
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: 'var(--accent-ai, #a855f7)' }}
            />
            {section.title}
          </h3>
          
          {/* Section Content */}
          <div className="pl-4 space-y-1.5">
            {section.items.map((item, itemIdx) => {
              // Check if it's an "omitted" note
              const isOmitted = item.startsWith('*Section omitted') || item.startsWith('*Note:');
              
              return (
                <p
                  key={itemIdx}
                  className={cn(
                    "text-sm leading-relaxed",
                    isOmitted && "italic text-xs"
                  )}
                  style={{ 
                    color: isOmitted ? 'var(--text-ghost)' : 'var(--text-secondary)' 
                  }}
                >
                  {isOmitted ? (
                    item.replace(/^\*/, '').replace(/\*$/, '')
                  ) : (
                    renderInlineMarkdown(item)
                  )}
                </p>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
