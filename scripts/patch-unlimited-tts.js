import fs from 'node:fs';

const path = 'index.html';
let s = fs.readFileSync(path, 'utf8');

// Restore the intended 5,000-character app limit.
s = s.replace(/စာဘယ်လောက်ရှည်ရှည် ထုတ်နိုင်ပါတယ်။/g, 'စာလုံး 5,000 အထိ ထည့်ပြီး အသံထုတ်နိုင်ပါတယ်။');
s = s.replace(/5,000 characters အထိ အသုံးပြုနိုင်ပါတယ်။/g, 'စာလုံး 5,000 အထိ ထည့်ပြီး အသံထုတ်နိုင်ပါတယ်။');
s = s.replace(/maxlength="5000"/g, '');

// Remove the previous unlimited-TTS injection if it was already applied.
const marker = '<!-- UNLIMITED-TTS-V1 -->';
const markerIndex = s.indexOf(marker);
if (markerIndex !== -1) {
  const endMarker = '</script>';
  const endIndex = s.indexOf(endMarker, markerIndex);
  if (endIndex !== -1) s = s.slice(0, markerIndex) + s.slice(endIndex + endMarker.length);
}

// Add a real maxlength and restore a 0 / 5,000 counter while preserving the existing UI.
s = s.replace(/<textarea id="text"\s*/g, '<textarea id="text" maxlength="5000" ');
s = s.replace(/<span id="counter">[^<]*<\/span>/g, '<span id="counter">0 / 5,000</span>');

// Add a small client-side guard before the existing generate handler.
if (!s.includes('<!-- TTS-LIMIT-5000 -->')) {
  const patch = `<!-- TTS-LIMIT-5000 -->\n<script>\n(function(){\n  function installLimit(){\n    const text=document.getElementById('text');\n    const counter=document.getElementById('counter');\n    const button=document.getElementById('generate');\n    if(!text||!counter||!button||button.dataset.limit5000Installed)return;\n    button.dataset.limit5000Installed='1';\n    const update=()=>{\n      if(text.value.length>5000) text.value=text.value.slice(0,5000);\n      counter.textContent=text.value.length.toLocaleString()+' / 5,000';\n    };\n    text.addEventListener('input',update);\n    button.addEventListener('click',function(e){\n      if(text.value.length>5000){\n        e.preventDefault();\n        e.stopImmediatePropagation();\n        counter.textContent='5,000 / 5,000';\n        const status=document.getElementById('status');\n        if(status)status.textContent='❌ စာသားအရှည်သည် 5,000 characters ထက် မကျော်ရပါ။';\n      }\n    },true);\n    update();\n  }\n  window.addEventListener('DOMContentLoaded',installLimit);\n  setTimeout(installLimit,100);\n  setTimeout(installLimit,800);\n})();\n</script>\n`;
  s = s.replace('</body>', patch + '</body>');
}

fs.writeFileSync(path, s, 'utf8');
console.log('Restored 5,000-character TTS limit.');
