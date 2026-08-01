import time
from playwright.sync_api import sync_playwright
URL="http://localhost:8731/viewer.html"
OUT="/Users/taku/Library/CloudStorage/OneDrive-UCSanDiego/Claude/BrainModel/brain_model/"
msgs=[]; errors=[]
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=angle","--use-angle=metal","--ignore-gpu-blocklist","--enable-gpu"])
    pg=b.new_page(viewport={"width":1500,"height":950}, device_scale_factor=2)
    pg.on("console", lambda m: msgs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    # inject an FPS meter before load
    pg.add_init_script("""
      window.__frames=0; window.__t0=performance.now();
      (function tick(){ window.__frames++; requestAnimationFrame(tick); })();
      window.__fps=()=>{ const dt=(performance.now()-window.__t0)/1000; return window.__frames/dt; };
    """)
    pg.goto(URL, wait_until="load")
    ok=False
    for _ in range(80):
        try:
            if pg.evaluate("()=>window.__ready&&window.__ready()"): ok=True;break
        except: pass
        time.sleep(0.5)
    print("READY:",ok)
    print("HUD:", pg.evaluate("()=>document.getElementById('hud').textContent"))

    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT+"full_front.png")

    # cortex translucent (xray) all structures
    pg.click("#btnXray"); pg.wait_for_timeout(500)
    pg.click("#views button[title='left']"); pg.wait_for_timeout(500)
    pg.screenshot(path=OUT+"full_left_xray.png")
    pg.click("#views button[title='top']"); pg.wait_for_timeout(500)
    pg.screenshot(path=OUT+"full_top_xray.png")

    # coronal clip (structure colors), front view, full opacity cortex reload
    pg.reload(wait_until="load")
    for _ in range(80):
        try:
            if pg.evaluate("()=>window.__ready&&window.__ready()"): break
        except: pass
        time.sleep(0.5)
    pg.wait_for_timeout(500)
    # enable coronal clip, front view
    cbs=pg.query_selector_all("#clips .clip")
    cbs[1].query_selector("input[type=checkbox]").check()  # coronal (A-P)
    pg.click("#views button[title='front']"); pg.wait_for_timeout(500)
    pg.screenshot(path=OUT+"full_coronal.png")
    # switch to axial clip only
    cbs[1].query_selector("input[type=checkbox]").uncheck()
    cbs[2].query_selector("input[type=checkbox]").check()   # axial (S-I)
    pg.click("#views button[title='top']"); pg.wait_for_timeout(500)
    pg.screenshot(path=OUT+"full_axial.png")

    # measure FPS over ~2s of steady rendering
    pg.evaluate("()=>{window.__frames=0;window.__t0=performance.now();}")
    pg.wait_for_timeout(2000)
    fps=pg.evaluate("()=>window.__fps()")
    print("FPS (approx, headless):", round(fps,1))
    b.close()

print("\nCONSOLE (%d):"%len(msgs))
for m in msgs[-15:]: print(" ",m)
print("PAGE ERRORS (%d):"%len(errors))
for e in errors: print(" ",e)
