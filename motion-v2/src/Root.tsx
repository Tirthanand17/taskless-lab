import React from 'react';
import {Composition} from 'remotion';
import {CsvScannerShort} from './CsvScannerShort';
import {LeadingZeroShort} from './LeadingZeroShort';
import {LeadingZerosLong} from './LeadingZerosLong';
import {DateLocaleShort} from './DateLocaleShort';
import {DuplicateLatestShort} from './DuplicateLatestShort';
import {HiddenSpaceXrayShort} from './HiddenSpaceXrayShort';
import {InvisibleExcelLong} from './InvisibleExcelLong';

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
      <Composition
        id="LeadingZerosLong"
        component={LeadingZerosLong}
        durationInFrames={5160}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="DateLocaleShort"
        component={DateLocaleShort}
        durationInFrames={960}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="DuplicateLatestShort"
        component={DuplicateLatestShort}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="InvisibleExcelLong"
        component={InvisibleExcelLong}
        durationInFrames={5760}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="HiddenSpaceXrayShort"
        component={HiddenSpaceXrayShort}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
