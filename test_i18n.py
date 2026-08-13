import time
from playwright.sync_api import sync_playwright
OUT="/Users/taku/Library/CloudStorage/OneDrive-UCSanDiego/Claude/BrainModel/brain_model/"
msgs=[];errors=[]
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=angle","--use-angle=metal","--ignore-gpu-blocklist","--enable-gpu"])
    pg=b.new_page(viewport={"width":1400,"height":900}, device_scale_factor=2)
    pg.on("console", lambda m: msgs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("http://localhost:8731/viewer.html", wait_until="load")
    for _ in range(80):
        try:
            if pg.evaluate("()=>window.__ready&&window.__ready()"): break
        except: pass
        time.sleep(0.5)
    pg.wait_for_timeout(500)

    # default JA
    lang0=pg.evaluate("()=>document.documentElement.lang")
    h1_0=pg.evaluate("()=>document.querySelector('h1').textContent")
    btn0=pg.evaluate("()=>document.getElementById('btnLang').textContent")
    print(f"initial: lang={lang0} h1={h1_0!r} langBtn={btn0!r}")
    pg.screenshot(path=OUT+"i18n_ja.png")

    # set some state: hide cortex_L, set thalamus_L opacity 0.5, enable coronal clip
    pg.evaluate("""()=>{
      const v=document.getElementById('vis_Cortex_L'); v.checked=false; v.dispatchEvent(new Event('change'));
      const clips=document.querySelectorAll('#clips .clip');
      const cb=clips[1].querySelector('input[type=checkbox]'); cb.checked=true; cb.dispatchEvent(new Event('change'));
      const sl=clips[1].querySelector('input[type=range]'); sl.value=(+sl.min)+(+sl.max-+sl.min)*0.5; sl.dispatchEvent(new Event('input'));
    }""")
    # select a structure to populate info panel
    pg.evaluate("()=>{ const lbls=[...document.querySelectorAll('#tree label')]; const t=lbls.find(l=>l.title.includes('Thalamus')||l.textContent.includes('視床')); if(t) t.click(); }")
    pg.wait_for_timeout(300)
    state_before=pg.evaluate("""()=>({
      cortexL_vis: document.getElementById('vis_Cortex_L').checked,
      coronal_on: document.querySelectorAll('#clips .clip')[1].querySelector('input[type=checkbox]').checked,
      coronal_val: document.querySelectorAll('#clips .clip')[1].querySelector('input[type=range]').value,
      info_shown: document.getElementById('info').style.display,
    })""")
    print("state before toggle:", state_before)

    # toggle to EN
    pg.click("#btnLang"); pg.wait_for_timeout(400)
    lang1=pg.evaluate("()=>document.documentElement.lang")
    h1_1=pg.evaluate("()=>document.querySelector('h1').textContent")
    btn1=pg.evaluate("()=>document.getElementById('btnLang').textContent")
    views1=pg.evaluate("()=>[...document.querySelectorAll('#views button')].map(b=>b.textContent)")
    clips1=pg.evaluate("()=>[...document.querySelectorAll('#clips .clip span')].map(s=>s.textContent)")
    tree1=pg.evaluate("()=>[...document.querySelectorAll('#tree label')].slice(0,4).map(l=>l.textContent)")
    info1=pg.evaluate("()=>document.getElementById('info').innerText")
    hud1=pg.evaluate("()=>document.getElementById('hud').textContent")
    print(f"after EN: lang={lang1} h1={h1_1!r} langBtn={btn1!r}")
    print("  views:", views1)
    print("  clips:", clips1)
    print("  tree[0:4]:", tree1)
    print("  hud:", hud1)
    print("  info panel:", repr(info1))
    state_after=pg.evaluate("""()=>({
      cortexL_vis: document.getElementById('vis_Cortex_L').checked,
      coronal_on: document.querySelectorAll('#clips .clip')[1].querySelector('input[type=checkbox]').checked,
      coronal_val: document.querySelectorAll('#clips .clip')[1].querySelector('input[type=range]').value,
      info_shown: document.getElementById('info').style.display,
    })""")
    print("state after toggle:", state_after)
    print("STATE PRESERVED:", state_before==state_after)
    pg.screenshot(path=OUT+"i18n_en.png")

    # toggle back to JA
    pg.click("#btnLang"); pg.wait_for_timeout(300)
    print("back to:", pg.evaluate("()=>document.documentElement.lang"), pg.evaluate("()=>document.querySelector('h1').textContent"))
    b.close()

print("\nCONSOLE (non-ReadPixels):")
for m in msgs:
    if "ReadPixels" not in m: print("  ",m)
print("PAGE ERRORS (%d):"%len(errors))
for e in errors: print("  ",e)
