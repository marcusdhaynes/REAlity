export function comparePixels(a,b,width,height,tolerance=12){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>16000000||a.length!==width*height*4||b.length!==a.length)throw Error('Dimensions or pixel data invalid');
 if(!Number.isInteger(tolerance)||tolerance<0||tolerance>255)throw Error('Tolerance must be 0–255');
 let mismatch=0,total=0;const diff=new Uint8ClampedArray(a.length);
 for(let i=0;i<a.length;i+=4){let max=0;for(let c=0;c<4;c++){let d=Math.abs(a[i+c]-b[i+c]);max=Math.max(max,d);total+=d;}if(max>tolerance){mismatch++;diff[i]=255;diff[i+1]=40;diff[i+2]=110;}else{let grey=Math.round((a[i]+a[i+1]+a[i+2])/9);diff[i]=diff[i+1]=diff[i+2]=grey;}diff[i+3]=255;}
 return {diff,report:{width,height,tolerance,changedPixels:mismatch,totalPixels:width*height,changedPercent:100*mismatch/(width*height),meanAbsoluteChannelError:total/a.length,scope:'Visual comparison only; not functional equivalence'}};
}
