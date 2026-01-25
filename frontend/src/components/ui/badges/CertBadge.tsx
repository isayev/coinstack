/**
 * CertBadge - Certification service badge (NGC, PCGS, ANACS)
 * 
 * Shows the grading service with clickable link to verification
 */

import { cn } from "@/lib/utils";
import { ExternalLink } from "lucide-react";

type CertService = 'ngc' | 'pcgs' | 'anacs' | 'raw' | 'self';

interface CertConfig {
  label: string;
  cssVar: string;
  verifyUrl?: (certNumber: string) => string;
}

const CERT_CONFIG: Record<CertService, CertConfig> = {
  ngc: {
    label: 'NGC',
    cssVar: 'ngc',
    verifyUrl: (cert) => `https://www.ngccoin.com/certlookup/${cert}/`,
  },
  pcgs: {
    label: 'PCGS',
    cssVar: 'pcgs',
    verifyUrl: (cert) => `https://www.pcgs.com/cert/${cert}`,
  },
  anacs: {
    label: 'ANACS',
    cssVar: 'anacs',
    verifyUrl: (cert) => `https://www.anacs.com/verify/${cert}`,
  },
  raw: {
    label: 'Raw',
    cssVar: 'unknown',
  },
  self: {
    label: 'Self',
    cssVar: 'unknown',
  },
};

function normalizeService(service: string | null | undefined): CertService {
  if (!service) return 'raw';
  const s = service.toLowerCase().trim();
  if (s === 'ngc') return 'ngc';
  if (s === 'pcgs') return 'pcgs';
  if (s === 'anacs') return 'anacs';
  if (s === 'self' || s === 'none' || s === 'self-graded') return 'self';
  return 'raw';
}

interface CertBadgeProps {
  service: string | null | undefined;
  certNumber?: string | null;
  size?: 'sm' | 'md' | 'lg';
  showVerifyLink?: boolean;
  className?: string;
}

export function CertBadge({
  service,
  certNumber,
  size = 'md',
  showVerifyLink = true,
  className,
}: CertBadgeProps) {
  const normalizedService = normalizeService(service);
  const config = CERT_CONFIG[normalizedService];
  
  // Don't show badge for raw/self graded
  if (normalizedService === 'raw' || normalizedService === 'self') {
    return null;
  }
  
  const hasVerifyUrl = config.verifyUrl && certNumber;

  const sizeClasses = {
    sm: 'h-[22px] text-[10px] px-1.5 gap-0.5',
    md: 'h-[28px] text-xs px-2 gap-1',
    lg: 'h-[36px] text-sm px-3 gap-1.5',
  };

  const handleClick = (e: React.MouseEvent) => {
    if (hasVerifyUrl) {
      e.stopPropagation();
      window.open(config.verifyUrl!(certNumber!), '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div
      role={hasVerifyUrl ? 'button' : undefined}
      tabIndex={hasVerifyUrl ? 0 : undefined}
      onClick={handleClick}
      onKeyDown={hasVerifyUrl ? (e) => e.key === 'Enter' && handleClick(e as any) : undefined}
      className={cn(
        'inline-flex items-center justify-center rounded font-bold',
        'transition-all duration-200',
        sizeClasses[size],
        hasVerifyUrl && 'cursor-pointer hover:brightness-110',
        className
      )}
      style={{
        background: `var(--cert-${config.cssVar})`,
        color: '#ffffff',
      }}
      title={certNumber ? `${config.label} #${certNumber} - Click to verify` : config.label}
    >
      <span>{config.label}</span>
      {showVerifyLink && hasVerifyUrl && (
        <ExternalLink className="w-3 h-3 opacity-70" />
      )}
    </div>
  );
}

/**
 * CertificationSummary - Shows distribution of certified vs raw coins
 */
interface CertDistribution {
  service: string;
  count: number;
}

interface CertificationSummaryProps {
  certifications: CertDistribution[];
  totalCoins: number;
  onServiceClick?: (service: string) => void;
  className?: string;
}

export function CertificationSummary({
  certifications,
  totalCoins,
  onServiceClick,
  className,
}: CertificationSummaryProps) {
  const certifiedCount = certifications
    .filter(c => c.service.toLowerCase() !== 'raw' && c.service.toLowerCase() !== 'self')
    .reduce((sum, c) => sum + c.count, 0);
  
  const certifiedPct = totalCoins > 0 ? Math.round((certifiedCount / totalCoins) * 100) : 0;

  return (
    <div className={cn('space-y-3', className)}>
      {/* Service breakdown */}
      <div className="space-y-2">
        {certifications.map(({ service, count }) => {
          const normalizedService = normalizeService(service);
          const config = CERT_CONFIG[normalizedService];
          const isClickable = !!onServiceClick && count > 0;
          
          return (
            <div
              key={service}
              role={isClickable ? 'button' : undefined}
              tabIndex={isClickable ? 0 : undefined}
              onClick={() => isClickable && onServiceClick(service)}
              className={cn(
                'flex items-center justify-between p-2 rounded',
                'transition-all duration-200',
                isClickable && 'cursor-pointer hover:bg-[var(--bg-hover)]',
                count === 0 && 'opacity-50'
              )}
              style={{
                background: 'var(--bg-elevated)',
              }}
            >
              <div className="flex items-center gap-2">
                {normalizedService !== 'raw' && normalizedService !== 'self' ? (
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ background: `var(--cert-${config.cssVar})` }}
                  />
                ) : (
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ background: 'var(--text-ghost)' }}
                  />
                )}
                <span 
                  className="text-sm font-medium"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {config.label}
                </span>
              </div>
              <span 
                className="text-sm font-bold"
                style={{ color: 'var(--text-secondary)' }}
              >
                {count}
              </span>
            </div>
          );
        })}
      </div>
      
      {/* Certified percentage */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span style={{ color: 'var(--text-muted)' }}>Certified</span>
          <span style={{ color: 'var(--text-secondary)' }}>{certifiedPct}%</span>
        </div>
        <div 
          className="h-2 rounded-full overflow-hidden"
          style={{ background: 'var(--bg-elevated)' }}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${certifiedPct}%`,
              background: 'var(--cert-ngc)', // Use NGC blue as certified color
            }}
          />
        </div>
      </div>
    </div>
  );
}
