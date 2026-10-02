import React from 'react';
import {Composition} from 'remotion';
import {CsvScannerShort} from './CsvScannerShort';
import {LeadingZeroShort} from './LeadingZeroShort';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CsvScannerShort"
        component={CsvScannerShort}
        durationInFrames={930}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="LeadingZeroShort"
        component={LeadingZeroShort}
        durationInFrames={870}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
