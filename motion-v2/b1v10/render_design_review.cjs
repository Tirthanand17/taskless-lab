const path = require('path');
const fs = require('fs');
const {bundle} = require('@remotion/bundler');
const {selectComposition,renderStill} = require('@remotion/renderer');
(async()=>{
  const out = path.resolve(process.argv[2] || 'design-review-v020');
  fs.mkdirSync(out,{recursive:true});
  const url = await bundle({entryPoint:path.join(__dirname,'design-demo.tsx'),onProgress:()=>{}});
  for (const [id,label] of [['B1v10DesignVertical','vertical'],['B1v10DesignLandscape','landscape']]) {
    const composition=await selectComposition({serveUrl:url,id,logLevel:'error'});
    for (const frame of [15,75]) {
      const output=path.join(out,label+'-'+frame+'.png');
      await renderStill({serveUrl:url,composition,frame,output,imageFormat:'png',logLevel:'error',overwrite:true});
      console.log('RENDERED',label,frame,composition.width,composition.height,fs.statSync(output).size);
    }
  }
})().catch(e=>{console.error(e);process.exitCode=1});
