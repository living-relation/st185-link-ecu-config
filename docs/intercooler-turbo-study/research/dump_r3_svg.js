const fs=require("fs"),{JSDOM,VirtualConsole}=require("jsdom");
const vc=new VirtualConsole();
const d=new JSDOM(fs.readFileSync("intercooler-report.html","utf8"),
  {runScripts:"dangerously",virtualConsole:vc,pretendToBeVisual:true});
setTimeout(()=>{
  const ids=["ch_r3_power","ch_r3_ladder","ch_r3_sens","ch_r3_ve","ch_r3_turbo","ch_r3_core","ch_pulse","ch_bp","ch_spoolpair"];
  fs.mkdirSync("data/r3svg",{recursive:true});
  ids.forEach(id=>{
    const s=d.window.document.getElementById(id).querySelector("svg");
    const vb=s.getAttribute("viewBox").split(" ");
    s.setAttribute("width",vb[2]); s.setAttribute("height",vb[3]);
    const wrap='<svg xmlns="http://www.w3.org/2000/svg" width="'+vb[2]+'" height="'+vb[3]+'">'
      +'<rect width="100%" height="100%" fill="#0d1117"/>'+s.innerHTML+'</svg>';
    fs.writeFileSync("data/r3svg/"+id+".svg",wrap);
  });
  console.log("dumped "+ids.length);
},2500);
