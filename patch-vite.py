import pathlib
f = pathlib.Path("node_modules/vite/dist/node/chunks/config.js")
t = f.read_text()
old = 'if (!styles.has(id)) throw new Error(`css content for ${JSON.stringify(id)} was not found`);'
new = 'if (!styles.has(id)) continue;'
if old in t:
    t = t.replace(old, new)
    f.write_text(t)
    print("Patched Vite css-post successfully")
else:
    print("Pattern not found - Vite may already be patched or version changed")
