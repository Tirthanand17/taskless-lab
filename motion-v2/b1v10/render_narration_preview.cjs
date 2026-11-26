const fs=require('fs');const path=require('path');
const {bundle}=require('@remotion/bundler');const {selectComposition,renderStill}=require('@remotion/renderer');
(async()=>{const out=path.resolve(process.argv[2]||'narration-caption-preview');fs.mkdirSync(out,{recursive:true});
const url=await bundle({entryPoint:path.join(__dirname,'narration-caption-demo.tsx'),onProgress:()=>{}});
for(const [id,frame] of [['NarrationVertical',51],['NarrationLandscape',51],['NarrationVertical',400]]){
 const composition=await selectComposition({serveUrl:url,id,logLevel:'error'});
 const name=id+'-'+frame+'.png';
 await renderStill({serveUrl:url,composition,frame,output:path.join(out,name),imageFormat:'png',logLevel:'error',overwrite:true});
 console.log('RENDERED',name,composition.width,composition.height);
}
})().catch(e=>{console.error(e);process.exitCode=1});
