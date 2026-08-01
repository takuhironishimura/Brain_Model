import sys, time
from playwright.sync_api import sync_playwright
URL="http://localhost:8731/viewer.html"
OUT="/Users/taku/Library/CloudStorage/OneDrive-UCSanDiego/Claude/BrainModel/brain_model/"
mode=sys.argv[1] if len(sys.argv)>1 else "hard"
msgs=[];errors=[]
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=angle","--use-angle=metal","--ignore-gpu-blocklist","--enable-gpu"])
    pg=b.new_page(viewport={"width":1500,"height":950}, device_scale_factor=2)
    pg.on("console", lambda m: msgs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.add_init_script("""window.__frames=0;window.__t0=performance.now();
      (function t(){window.__frames++;requestAnimationFrame(t);})();
      window.__fps=()=>window.__frames/((performance.now()-window.__t0)/1000);""")
    pg.goto(URL, wait_until="load")
    for _ in range(80):
        try:
            if pg.evaluate("()=>window.__ready&&window.__ready()"): break
        except: pass
        time.sleep(0.5)
    pg.wait_for_timeout(600)

    def only(keep):
        pg.evaluate("""(keep)=>{
          document.querySelectorAll('#tree input[type=checkbox][id^=vis_]').forEach(cb=>{
            const name=cb.id.slice(4); const want=keep.includes(name);
            if(cb.checked!==want){ cb.checked=want; cb.dispatchEvent(new Event('change')); }
          });
        }""", keep)

    def clip(axis_idx, frac):
        # enable one clip plane (0=sag,1=cor,2=axi), set slider to frac of range
        pg.evaluate("""([idx,frac])=>{
          const clips=document.querySelectorAll('#clips .clip');
          clips.forEach((c,i)=>{ const cb=c.querySelector('input[type=checkbox]');
            const want=(i===idx); if(cb.checked!==want){cb.checked=want; cb.dispatchEvent(new Event('change'));}});
          const c=clips[idx]; const sl=c.querySelector('input[type=range]');
          sl.value=(+sl.min)+(+sl.max-+sl.min)*frac; sl.dispatchEvent(new Event('input'));
        }""", [axis_idx, frac])

    if mode=="hard":
        only(["Cortex_L","Cortex_R","Thalamus_L","Thalamus_R","ThirdVentricle",
              "LateralVentricle_L","LateralVentricle_R"])
        clip(2, 0.55)                 # axial
        pg.click("#views button[title='top']"); pg.wait_for_timeout(600)
        pg.screenshot(path=OUT+"cap_hard_axial.png")
        # also an oblique view to see the cap face
        pg.click("#views button[title='front']")
        pg.evaluate("()=>{}"); pg.wait_for_timeout(300)
        # rotate a bit via setting camera? just front is fine
        pg.screenshot(path=OUT+"cap_hard_front.png")
    else:  # full all structures, 3 section directions
        clip(2,0.5); pg.click("#views button[title='top']"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT+"cap_full_axial.png")
        clip(1,0.5); pg.click("#views button[title='front']"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT+"cap_full_coronal.png")
        clip(0,0.5); pg.click("#views button[title='left']"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT+"cap_full_sagittal.png")
        pg.evaluate("()=>{window.__frames=0;window.__t0=performance.now();}")
        pg.wait_for_timeout(2000)
        print("FPS:", round(pg.evaluate("()=>window.__fps()"),1))
    b.close()
print("CONSOLE(%d):"%len(msgs))
for m in msgs[-12:]:
    if "ReadPixels" not in m: print("  ",m)
print("ERRORS(%d):"%len(errors))
for e in errors: print("  ",e)
