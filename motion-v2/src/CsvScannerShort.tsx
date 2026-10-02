import React, {CSSProperties} from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const C = {
  bg: '#07111f',
  panel: '#0d1b2f',
  panel2: '#122640',
  line: '#24405f',
  text: '#f4f8fc',
  muted: '#9fb3c8',
  cyan: '#58e6ff',
  green: '#72efaa',
  red: '#ff7474',
  yellow: '#ffd86b',
};

const captionItems = [
  [0, 84, "That spreadsheet looks clean. It isn't."],
  [84, 180, 'AI can catch the problems you usually miss.'],
  [180, 276, 'Trailing spaces. Mixed email casing.'],
  [276, 372, 'Unstable headers. Duplicate rows.'],
  [372, 492, "Don't let it silently delete anything."],
  [492, 603, 'Flag the problems first.'],
  [603, 744, 'Then generate a validation summary.'],
  [744, 822, 'Review the flagged rows, then export.'],
  [822, 930, 'Faster cleanup — and cleanup you can verify.'],
] as const;

const clamp = (frame: number, input: number[], output: number[]) =>
  interpolate(frame, input, output, {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.2, 0.7, 0.2, 1),
  });

const GlowDot: React.FC<{color: string; size?: number}> = ({color, size = 12}) => (
  <span
    style={{
      width: size,
      height: size,
      borderRadius: '50%',
      background: color,
      boxShadow: `0 0 18px ${color}`,
      display: 'inline-block',
      flex: '0 0 auto',
    }}
  />
);

const Chip: React.FC<{
  text: string;
  color: string;
  style?: CSSProperties;
  opacity?: number;
  scale?: number;
}> = ({text, color, style, opacity = 1, scale = 1}) => (
  <div
    style={{
      position: 'absolute',
      padding: '14px 20px',
      borderRadius: 999,
      background: 'rgba(6,13,24,.92)',
      border: `1px solid ${color}88`,
      color,
      fontSize: 28,
      fontWeight: 800,
      letterSpacing: 0.2,
      boxShadow: `0 14px 45px rgba(0,0,0,.28), 0 0 24px ${color}20`,
      opacity,
      transform: `scale(${scale})`,
      ...style,
    }}
  >
    {text}
  </div>
);

const Caption: React.FC = () => {
  const frame = useCurrentFrame();
  const item = captionItems.find(([from, to]) => frame >= from && frame < to);
  if (!item) return null;
  const [from, to, text] = item;
  const intro = clamp(frame, [from, from + 6], [0, 1]);
  const outro = clamp(frame, [to - 7, to], [1, 0]);
  const opacity = Math.min(intro, outro);
  return (
    <div
      style={{
        position: 'absolute',
        left: 118,
        right: 118,
        top: 1495,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
        opacity,
      }}
    >
      <div
        style={{
          maxWidth: 850,
          padding: '13px 22px 15px',
          borderRadius: 18,
          background: 'rgba(3,8,15,.70)',
          border: '1px solid rgba(255,255,255,.10)',
          boxShadow: '0 10px 30px rgba(0,0,0,.28)',
          color: C.text,
          fontSize: 43,
          lineHeight: 1.14,
          fontWeight: 650,
          textAlign: 'center',
          whiteSpace: 'nowrap',
        }}
      >
        {text}
      </div>
    </div>
  );
};

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const drift = (frame * 0.45) % 80;
  return (
    <AbsoluteFill
      style={{
        background:
          'radial-gradient(circle at 50% 18%, #102d49 0%, #091827 34%, #07111f 68%, #040a12 100%)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: -200,
          opacity: 0.34,
          transform: `perspective(900px) rotateX(69deg) translateY(${260 + drift}px)`,
          transformOrigin: 'center top',
          backgroundImage:
            'linear-gradient(rgba(88,230,255,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(88,230,255,.12) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          maskImage: 'linear-gradient(to bottom, transparent, black 26%, black 80%, transparent)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 720,
          height: 720,
          borderRadius: '50%',
          left: 180,
          top: 390,
          background: 'rgba(88,230,255,.08)',
          filter: 'blur(100px)',
        }}
      />
    </AbsoluteFill>
  );
};

const Header: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      top: 58,
      left: 62,
      right: 62,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      color: C.muted,
      fontSize: 24,
      fontWeight: 800,
      letterSpacing: 1.6,
    }}
  >
    <span>FLOWMINUTE LAB</span>
    <span style={{color: C.cyan}}>DATA CLEANING / 01</span>
  </div>
);

const Spreadsheet: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, mass: 0.8, stiffness: 90}});
  const clean = clamp(frame, [330, 465], [0, 1]);
  const final = clamp(frame, [720, 850], [0, 1]);

  const rotateY = 11 - clean * 7 - final * 3;
  const rotateX = 7 - clean * 3;
  const scale = 0.88 + enter * 0.08 + final * 0.05;
  const x = -8 + final * 22;
  const y = 275 - enter * 30 - final * 40;

  const scanY = clamp(frame, [75, 330], [120, 1050]);
  const scanOpacity = clamp(frame, [60, 85, 315, 342], [0, 1, 1, 0]);

  const issue1 = clamp(frame, [105, 125], [0, 1]) * (1 - clean);
  const issue2 = clamp(frame, [150, 170], [0, 1]) * (1 - clean);
  const issue3 = clamp(frame, [205, 225], [0, 1]) * (1 - clean);
  const issue4 = clamp(frame, [255, 275], [0, 1]) * (1 - clean);

  const rows = [
    ['1001', clean > 0.45 ? 'alice@example.com' : 'ALICE@EXAMPLE.COM␠', 'Alice', 'Active'],
    ['1002', 'bob@example.com', 'Bob', 'Active'],
    ['1003', 'maya@example.com', 'Maya', 'Pending'],
    ['1003', 'maya@example.com', 'Maya', 'Pending'],
  ];

  return (
    <div
      style={{
        position: 'absolute',
        left: 78,
        top: y,
        width: 924,
        height: 1050,
        perspective: 1600,
        transformStyle: 'preserve-3d',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateX(${x}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scale})`,
          transformOrigin: 'center center',
          transformStyle: 'preserve-3d',
          borderRadius: 36,
          background: 'linear-gradient(155deg, #122640 0%, #0b192d 60%, #091525 100%)',
          border: '1px solid rgba(145,190,225,.23)',
          boxShadow: '0 50px 120px rgba(0,0,0,.42), 0 0 60px rgba(88,230,255,.09)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: 95,
            padding: '0 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#102238',
            borderBottom: `1px solid ${C.line}`,
          }}
        >
          <div style={{display: 'flex', gap: 12}}>
            {[C.red, C.yellow, C.green].map((color) => (
              <GlowDot key={color} color={color} size={14} />
            ))}
          </div>
          <div style={{color: C.text, fontSize: 27, fontWeight: 800}}>customers_oct.csv</div>
          <div style={{color: C.muted, fontSize: 22}}>1,248 rows</div>
        </div>

        <div style={{padding: '28px 26px 36px'}}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '160px 330px 190px 170px',
              gap: 8,
              marginBottom: 10,
            }}
          >
            {[
              clean > 0.55 ? 'customer_id' : 'Customer ID ',
              'email',
              'name',
              'status',
            ].map((h, i) => (
              <div
                key={i}
                style={{
                  background: clean > 0.55 ? 'rgba(114,239,170,.12)' : '#162b47',
                  border: `1px solid ${clean > 0.55 ? C.green + '55' : C.line}`,
                  borderRadius: 12,
                  padding: '17px 14px',
                  color: clean > 0.55 ? C.green : C.text,
                  fontSize: 23,
                  fontWeight: 800,
                }}
              >
                {h}
              </div>
            ))}
          </div>

          {rows.map((row, r) => {
            const duplicateFade = r === 3 ? clamp(frame, [440, 515], [1, 0.24]) : 1;
            const duplicateShift = r === 3 ? clamp(frame, [440, 515], [0, 105]) : 0;
            return (
              <div
                key={r}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '160px 330px 190px 170px',
                  gap: 8,
                  marginBottom: 8,
                  opacity: duplicateFade,
                  transform: `translateX(${duplicateShift}px)`,
                }}
              >
                {row.map((cell, c) => {
                  let problem = false;
                  if (r === 0 && c === 1 && issue1 + issue2 > 0.5) problem = true;
                  if (r === 3 && issue4 > 0.5) problem = true;
                  return (
                    <div
                      key={c}
                      style={{
                        position: 'relative',
                        minHeight: 66,
                        display: 'flex',
                        alignItems: 'center',
                        padding: '0 14px',
                        borderRadius: 11,
                        background: problem
                          ? 'rgba(255,116,116,.13)'
                          : clean > 0.55
                            ? 'rgba(114,239,170,.055)'
                            : '#0e2036',
                        border: `1px solid ${problem ? C.red + '66' : '#1e3854'}`,
                        color: problem ? '#ffdada' : C.text,
                        fontSize: 22,
                        fontWeight: c === 0 ? 800 : 600,
                      }}
                    >
                      {cell}
                      {problem && (
                        <span
                          style={{
                            position: 'absolute',
                            right: 10,
                            width: 9,
                            height: 9,
                            borderRadius: 9,
                            background: C.red,
                            boxShadow: `0 0 14px ${C.red}`,
                          }}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>

        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: scanY,
            height: 6,
            opacity: scanOpacity,
            background: `linear-gradient(90deg, transparent, ${C.cyan}, transparent)`,
            boxShadow: `0 0 24px ${C.cyan}, 0 0 70px ${C.cyan}66`,
          }}
        />

        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 36,
            border: `2px solid rgba(88,230,255,${0.15 + scanOpacity * 0.2})`,
            pointerEvents: 'none',
          }}
        />
      </div>

      <Chip text="TRAILING SPACE" color={C.red} opacity={issue1} scale={0.9 + issue1 * 0.1} style={{left: 520, top: 290}} />
      <Chip text="MIXED CASING" color={C.yellow} opacity={issue2} scale={0.9 + issue2 * 0.1} style={{left: 70, top: 465}} />
      <Chip text="HEADER DRIFT" color={C.red} opacity={issue3} scale={0.9 + issue3 * 0.1} style={{left: 540, top: 90}} />
      <Chip text="DUPLICATE" color={C.red} opacity={issue4} scale={0.9 + issue4 * 0.1} style={{left: 580, top: 700}} />
    </div>
  );
};

const ReviewQueue: React.FC = () => {
  const frame = useCurrentFrame();
  const visible = clamp(frame, [395, 440, 590, 625], [0, 1, 1, 0]);
  const x = clamp(frame, [395, 455], [130, 0]);
  return (
    <div
      style={{
        position: 'absolute',
        right: 48,
        top: 690,
        width: 340,
        opacity: visible,
        transform: `translateX(${x}px)`,
        zIndex: 5,
      }}
    >
      <div
        style={{
          padding: 22,
          borderRadius: 24,
          background: 'rgba(9,19,33,.96)',
          border: `1px solid ${C.yellow}55`,
          boxShadow: '0 28px 70px rgba(0,0,0,.34)',
        }}
      >
        <div style={{fontSize: 22, color: C.yellow, fontWeight: 900, letterSpacing: 1.2}}>REVIEW QUEUE</div>
        <div style={{marginTop: 16, padding: 16, borderRadius: 15, background: '#16253b'}}>
          <div style={{fontSize: 27, color: C.text, fontWeight: 850}}>Customer 1003</div>
          <div style={{fontSize: 21, color: C.muted, marginTop: 5}}>duplicate row flagged</div>
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 10, marginTop: 15, color: C.muted, fontSize: 20}}>
          <GlowDot color={C.yellow} size={9} /> kept for human review
        </div>
      </div>
    </div>
  );
};

const ValidationPanel: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const introFrame = frame - 575;
  const enter = spring({frame: Math.max(0, introFrame), fps, config: {damping: 17, stiffness: 110}});
  const opacity = clamp(frame, [575, 615, 850, 900], [0, 1, 1, 0]);
  const y = 1160 - enter * 80;
  const stats = [
    ['1,248', 'rows in', C.cyan],
    ['37', 'duplicates', C.red],
    ['14', 'missing', C.yellow],
    ['4', 'columns fixed', C.green],
  ];
  return (
    <div
      style={{
        position: 'absolute',
        left: 88,
        right: 88,
        top: y,
        opacity,
        zIndex: 8,
      }}
    >
      <div
        style={{
          borderRadius: 28,
          padding: 24,
          background: 'rgba(7,16,28,.94)',
          border: '1px solid rgba(130,179,218,.20)',
          boxShadow: '0 28px 90px rgba(0,0,0,.40)',
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18}}>
          <span style={{fontSize: 25, color: C.text, fontWeight: 900}}>VALIDATION SUMMARY</span>
          <span style={{fontSize: 21, color: C.green, fontWeight: 850}}>✓ explainable changes</span>
        </div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12}}>
          {stats.map(([value, label, color], i) => {
            const itemEnter = clamp(frame, [610 + i * 14, 635 + i * 14], [0, 1]);
            return (
              <div
                key={label}
                style={{
                  minHeight: 126,
                  borderRadius: 20,
                  background: '#0d2035',
                  border: `1px solid ${String(color)}44`,
                  padding: '18px 16px',
                  opacity: itemEnter,
                  transform: `translateY(${(1 - itemEnter) * 22}px)`,
                }}
              >
                <div style={{fontSize: 40, color: String(color), fontWeight: 950}}>{value}</div>
                <div style={{fontSize: 19, color: C.muted, marginTop: 4, fontWeight: 700}}>{label}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const FinalBadge: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame: Math.max(0, frame - 790), fps, config: {damping: 14, stiffness: 115}});
  const opacity = clamp(frame, [785, 825], [0, 1]);
  return (
    <div
      style={{
        position: 'absolute',
        left: 250,
        right: 250,
        top: 250,
        opacity,
        transform: `scale(${0.8 + enter * 0.2}) translateY(${(1 - enter) * -35}px)`,
        zIndex: 10,
        textAlign: 'center',
      }}
    >
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 13,
          padding: '15px 28px',
          borderRadius: 999,
          background: 'rgba(14,49,39,.94)',
          border: `1px solid ${C.green}88`,
          color: C.green,
          fontSize: 29,
          fontWeight: 950,
          boxShadow: `0 0 42px ${C.green}20`,
        }}
      >
        <GlowDot color={C.green} size={11} />
        CLEANUP VERIFIED
      </div>
    </div>
  );
};

export const CsvScannerShort: React.FC = () => {
  return (
    <AbsoluteFill style={{fontFamily: 'Arial, Helvetica, sans-serif', color: C.text}}>
      <Background />
      <Header />
      <Spreadsheet />
      <ReviewQueue />
      <ValidationPanel />
      <FinalBadge />

      <Sequence from={0}>
        <Audio src={staticFile('voice.mp3')} volume={1} />
      </Sequence>

      <Caption />

      <div
        style={{
          position: 'absolute',
          left: 62,
          right: 62,
          bottom: 84,
          height: 2,
          background: 'rgba(255,255,255,.10)',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${(useCurrentFrame() / 929) * 100}%`,
            background: `linear-gradient(90deg,${C.cyan},${C.green})`,
            boxShadow: `0 0 12px ${C.cyan}66`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
