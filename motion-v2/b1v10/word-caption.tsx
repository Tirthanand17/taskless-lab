import React from 'react';
import {useCurrentFrame,useVideoConfig} from 'remotion';
import {Caption,C} from './visual-system';
export type TimedWord={word:string;start:number;end:number};
export type TimedCue={start:number;end:number;text:string;words:TimedWord[]};
export const activeCue=(cues:TimedCue[],time:number)=>cues.find(c=>c.start<=time && time<c.end);
export const WordCaption:React.FC<{cues:TimedCue[]}>=({cues})=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),t=f/fps;
 const cue=activeCue(cues,t);
 if(!cue)return null;
 return <Caption>{cue.words.map((w,i)=><React.Fragment key={i}>
  {i>0?' ':''}<span style={{color:w.start<=t&&t<w.end?C.lime:C.ink}}>{w.word}</span>
 </React.Fragment>)}</Caption>;
};
