import sys, time
from playwright.sync_api import sync_playwright

URL = "http://localhost:8731/viewer.html"
OUT = "/Users/taku/Library/CloudStorage/OneDrive-UCSanDiego/Claude/BrainModel/brain_model/"

msgs = []; errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width":1400,"height":900}, device_scale_factor=2)
    pg.on("console", lambda m: msgs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL, wait_until="load")
    # wait for model ready (loading overlay hidden)
    ok = False
    for _ in range(60):
        try:
            if pg.evaluate("() => window.__ready && window.__ready()"):
                ok = True; break
        except Exception:
            pass
        time.sleep(0.5)
    print("MODEL READY:", ok)

    # model dimensions + label world positions
    dims = pg.evaluate("""() => {
        return document.getElementById('hud').textContent;
    }""")
    print("HUD:", dims)

    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT+"v_front.png")

    # xray preset
    pg.click("#btnXray"); pg.wait_for_timeout(600)
    pg.screenshot(path=OUT+"v_front_xray.png")

    # left view (keep xray)
    pg.click("#views button[title='left']"); pg.wait_for_timeout(600)
    pg.screenshot(path=OUT+"v_left_xray.png")

    # top view
    pg.click("#views button[title='top']"); pg.wait_for_timeout(600)
    pg.screenshot(path=OUT+"v_top_xray.png")

    # a coronal clip enabled on full opacity front: reset then enable cor clip
    pg.click("#btnReset")
    # re-enable cortex opacity by reloading is simplest; instead just enable clip
    cbs = pg.query_selector_all("#clips .clip")
    if len(cbs) >= 2:
        cbs[1].query_selector("input[type=checkbox]").check()  # coronal
    pg.wait_for_timeout(500)
    pg.screenshot(path=OUT+"v_coronal_clip.png")

    b.close()

print("\n=== CONSOLE (%d) ===" % len(msgs))
for m in msgs[-40:]:
    print(m)
print("\n=== PAGE ERRORS (%d) ===" % len(errors))
for e in errors:
    print(e)
