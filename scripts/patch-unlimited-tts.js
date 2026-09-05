const fs = require('fs');
const path = 'index.html';
let s = fs.readFileSync(path, 'utf8');
let changed = false;

for (const [a, b] of [
  ['5,000 characters အထိ အသုံးပြုနိုင်ပါတယ်။', 'စာဘယ်လောက်ရှည်ရှည် ထုတ်နိုင်ပါတယ်။'],
  ['0 / 5,000', '0 characters'],
  ['maxlength="5000"', '']
]) {
  if (s.includes(a)) { s = s.split(a).join(b); changed = true; }
}

const marker = '<!-- UNLIMITED-TTS-V1 -->';
if (!s.includes(marker)) {
  const patch = String.raw`<!-- UNLIMITED-TTS-V1 -->
<script>
(function(){
  let controller=null;
  const CHUNK=2400;
  const $=id=>document.getElementById(id);
  function splitText(text){
    const out=[]; let rest=text.trim();
    while(rest.length>CHUNK){
      let cut=rest.lastIndexOf('။',CHUNK);
      if(cut<CHUNK*0.55) cut=rest.lastIndexOf(' ',CHUNK);
      if(cut<CHUNK*0.55) cut=CHUNK;
      const end=cut+(rest[cut]==='။'?1:0);
      out.push(rest.slice(0,end).trim()); rest=rest.slice(end).trim();
    }
    if(rest) out.push(rest); return out;
  }
  function decode(s){const bin=atob(s),a=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);return a;}
  function makeWav(parts){
    const dataLen=parts.reduce((n,p)=>n+p.length,0),out=new Uint8Array(44+dataLen),v=new DataView(out.buffer),e=new TextEncoder();
    out.set(e.encode('RIFF'),0);v.setUint32(4,36+dataLen,true);out.set(e.encode('WAVE'),8);out.set(e.encode('fmt '),12);v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,24000,true);v.setUint32(28,48000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);out.set(e.encode('data'),36);v.setUint32(40,dataLen,true);
    let pos=44;for(const p of parts){out.set(p,pos);pos+=p.length;}return out;
  }
  async function generateUnlimited(){
    const text=($('text')?.value||'').trim();if(!text)return;
    const button=$('generate'),status=$('status'),audio=$('audio'),download=$('download');
    const endpoint=($('ttsEndpoint')?.value||'/api/tts').trim()||'/api/tts';
    const chunks=splitText(text),parts=[];controller=new AbortController();if(button)button.disabled=true;
    if(status)status.textContent='AI Voice ထုတ်နေပါတယ်… 0 / '+chunks.length+' parts';
    try{
      for(let i=0;i<chunks.length;i++){
        const body={text:chunks[i],voice:$('voice')?.value||'Kore',style:$('style')?.value||'',language:window.currentLang||document.documentElement.lang||'my',speed:Number($('speed')?.value||1),volume:Number($('volume')?.value||1)};
        const r=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});
        const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||('TTS error '+r.status));
        const bytes=decode(d.audio||'');if(bytes.length<=44)throw new Error('AI Voice returned empty audio');parts.push(bytes.slice(44));
        if(status)status.textContent='AI Voice ထုတ်နေပါတယ်… '+(i+1)+' / '+chunks.length+' parts';
      }
      const url=URL.createObjectURL(new Blob([makeWav(parts)],{type:'audio/wav'}));if(window.__unlimitedAudioUrl)URL.revokeObjectURL(window.__unlimitedAudioUrl);window.__unlimitedAudioUrl=url;
      if(audio)audio.src=url;
      if(download){download.disabled=false;download.onclick=()=>{const a=document.createElement('a');a.href=url;a.download='gemini-ai-voice.wav';a.click();};}
      if(status)status.textContent='✓ အသံထုတ်ပြီးပါပြီ — '+text.length.toLocaleString()+' characters / '+chunks.length+' parts';
    }catch(e){if(status)status.textContent=e.name==='AbortError'?'ရပ်လိုက်ပါပြီ။':'❌ '+(e.message||'TTS failed');}
    finally{controller=null;if(button)button.disabled=false;}
  }
  function install(){
    const button=$('generate');if(!button||button.dataset.unlimitedInstalled)return;button.dataset.unlimitedInstalled='1';
    button.addEventListener('click',function(e){const ai=$('aiMode');if(ai&&!ai.classList.contains('active'))return;e.preventDefault();e.stopImmediatePropagation();generateUnlimited();},true);
    $('stop')?.addEventListener('click',()=>{if(controller)controller.abort();$('audio')?.pause();});
    const text=$('text'),counter=$('counter');if(text){text.removeAttribute('maxlength');text.addEventListener('input',()=>{if(counter)counter.textContent=text.value.length.toLocaleString()+' characters';});if(counter)counter.textContent=text.value.length.toLocaleString()+' characters';}
  }
  window.addEventListener('DOMContentLoaded',install);setTimeout(install,100);setTimeout(install,800);
})();
</script>
`;
  s = s.replace('</body>', patch + '</body>');
  changed = true;
}

fs.writeFileSync(path, s, 'utf8');
console.log(changed ? 'Unlimited TTS UI patched.' : 'No changes needed.');
