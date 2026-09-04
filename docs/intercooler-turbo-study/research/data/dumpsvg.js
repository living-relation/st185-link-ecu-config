const fs=require('fs'); const {JSDOM,VirtualConsole}=require('jsdom');
const html=fs.readFileSync('C:\\projects\\5sgte-intercooler-research\\intercooler-report.html','utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,
  virtualConsole:new VirtualConsole()});
setTimeout(()=>{
 const d=dom.window.document;
 ['ch_face','ch_soak','ch_fpi','ch_pipe','duct_svg','fit_plan','fit_front','tank_side','ch_dp','ch_vol']
 .forEach(id=>{
  const s=d.getElementById(id).querySelector('svg');
  s.setAttribute('xmlns','http://www.w3.org/2000/svg');
  const vb=s.getAttribute('viewBox').split(' ');
  s.setAttribute('width',vb[2]); s.setAttribute('height',vb[3]);
  const bg='<rect x="0" y="0" width="'+vb[2]+'" height="'+vb[3]+'" fill="#1a2029"/>';
  const out=s.outerHTML.replace('>',' >').replace(/^(<svg[^>]*>)/,'$1'+bg);
  fs.writeFileSync('svg_'+id+'.svg',out);
  console.log('wrote svg_'+id+'.svg  '+out.length+' bytes');
 });
},900);
