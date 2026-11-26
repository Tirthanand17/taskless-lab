import React from 'react';
import {useCurrentFrame} from 'remotion';
import {ease} from './visual-system';

export const CameraStage:React.FC<React.PropsWithChildren<{start:number;end:number}>>=({start,end,children})=>{
  const f=useCurrentFrame(), p=ease(f,start,end);
  return <div style={{height:'100%',width:'100%',position:'relative',overflow:'hidden',perspective:1100}}>
    <div style={{position:'absolute',inset:18,transformOrigin:'50% 52%',
      transform:'translate3d('+(-16*p)+'px,'+(-10*p)+'px,0) scale('+(1+.075*p)+') rotateY('+(-5+7*p)+'deg) rotateX('+(4-5*p)+'deg)'}}>
      {children}
    </div>
  </div>;
};
export const Reveal:React.FC<React.PropsWithChildren<{start:number;duration?:number}>>=({start,duration=12,children})=>{
  const f=useCurrentFrame(),p=ease(f,start,start+duration);
  return <div style={{opacity:p,transform:'translateY('+((1-p)*18)+'px)',width:'100%'}}>{children}</div>;
};
export const FocusLight:React.FC<{x:number;y:number}>=({x,y})=>
  <div style={{position:'absolute',inset:0,pointerEvents:'none',
    background:'radial-gradient(ellipse at '+x+'% '+y+'%,#72E3ED24,transparent 66%)'}}/>;
