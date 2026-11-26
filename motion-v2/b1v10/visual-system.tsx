import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import design from './design.json';

export const C = design.colors;
export type Region = {x:number;y:number;w:number;h:number};
export const useLayout = () => {
  const {width,height} = useVideoConfig();
  const layout = height > width ? design.formats.vertical : design.formats.landscape;
  if (width !== layout.width || height !== layout.height) throw new Error('Unsupported native canvas');
  return layout;
};
export const ease = (f:number,start:number,end:number) => interpolate(f,[start,end],[0,1],{
  extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)
});
export const Scene:React.FC<React.PropsWithChildren> = ({children}) => <AbsoluteFill style={{
  background:'radial-gradient(ellipse at 35% 30%, #18364A 0%, #0D1A28 48%, #09131F 84%)',
  color:C.ink,fontFamily:design.font,overflow:'hidden'
}}>{children}</AbsoluteFill>;
export const Zone:React.FC<React.PropsWithChildren<{region:Region;name:string}>> = ({region:r,name,children}) =>
  <div data-zone={name} style={{position:'absolute',left:r.x,top:r.y,width:r.w,height:r.h,boxSizing:'border-box',display:'flex',flexDirection:'column'}}>{children}</div>;
export const Kicker:React.FC<React.PropsWithChildren> = ({children}) => {
  const {type}=useLayout();
  return <div style={{fontSize:type.kicker,color:C.cyan,fontWeight:700,letterSpacing:2.4,lineHeight:1.2}}>{children}</div>;
};
export const Headline:React.FC<React.PropsWithChildren> = ({children}) => {
  const {type}=useLayout();
  return <div style={{fontSize:type.title,fontWeight:800,lineHeight:1.05,letterSpacing:-1.1,marginTop:14}}>{children}</div>;
};
export const Surface:React.FC<React.PropsWithChildren<{accent?:boolean}>> = ({children,accent=false}) =>
  <div style={{boxSizing:'border-box',height:'100%',padding:30,borderRadius:28,display:'flex',flexDirection:'column',
    background:'linear-gradient(145deg,#1B3448,#101F2E)',border:'2px solid '+(accent?C.cyan:C.edge),
    boxShadow:'0 16px 32px #050C1666'}}>{children}</div>;
export const Caption:React.FC<React.PropsWithChildren> = ({children}) => {
  const {type}=useLayout();
  return <div style={{margin:'auto 0',padding:'20px 28px',borderRadius:18,background:'#070F19',
    borderLeft:'6px solid '+C.lime,fontSize:type.caption,lineHeight:1.24,fontWeight:650}}>{children}</div>;
};
export const Chip:React.FC<{value:string;active:boolean}> = ({value,active}) =>
  <div style={{flex:'1 1 0',minWidth:0,textAlign:'center',borderRadius:14,padding:'15px 0',
    fontSize:48,lineHeight:1.12,fontWeight:800,fontVariantNumeric:'tabular-nums',
    background:active?'#284D55':C.panelLight,border:'2px solid '+(active?C.lime:C.edge),color:active?C.lime:C.ink}}>{value}</div>;
export const Rise:React.FC<React.PropsWithChildren<{start:number}>> = ({start,children}) => {
  const f=useCurrentFrame(),p=ease(f,start,start+12);
  return <div style={{opacity:p,transform:'translateY('+((1-p)*12)+'px)'}}>{children}</div>;
};
