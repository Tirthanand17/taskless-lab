const path=require('path');
const fs=require('fs');
const {bundle}=require('@remotion/bundler');
const {selectComposition,renderMedia}=require('@remotion/renderer');
(async()=>{
 const out=path.resolve(process.argv[2]||'motion-review-v040');
 fs.mkdirSync(out,{recursive:true});
 const url=await bundle({entryPoint:path.join(__dirname,'motion-benchmark.tsx'),onProgress:()=>{}});
 const composition=await selectComposition({serveUrl:url,id:'B1v10MotionQualityVertical',logLevel:'error'});
 await renderMedia({serveUrl:url,composition,codec:'h264',crf:18,pixelFormat:'yuv420p',concurrency:1,outputLocation:path.join(out,'motion-v040.mp4'),logLevel:'error',overwrite:true,onProgress:({renderedFrames})=>{if(renderedFrames&&renderedFrames%30===0)console.log('Rendered',renderedFrames);}});
 console.log('DONE',composition.width,composition.height,composition.durationInFrames);
})().catch(e=>{console.error(e);process.exitCode=1});
