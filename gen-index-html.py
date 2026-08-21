import os
import glob

client_dir = "dist/client"
assets_dir = os.path.join(client_dir, "assets")

# Patch client JS: replace hydrateRoot with createRoot for client-side rendering
# (since we're not running the SSR server, hydration will fail on empty #root)
for js_file in glob.glob(os.path.join(assets_dir, "*.js")):
    with open(js_file, "r") as f:
        content = f.read()
    if "hydrateRoot" in content:
        content = content.replace("hydrateRoot", "createRoot")
        with open(js_file, "w") as f:
            f.write(content)
        print(f"Patched hydrateRoot -> createRoot in {os.path.basename(js_file)}")

js_files = sorted(glob.glob(os.path.join(assets_dir, "index-*.js")))
css_files = sorted(glob.glob(os.path.join(assets_dir, "styles-*.css")))

if not js_files:
    print("ERROR: No index JS file found in dist/client/assets/")
    exit(1)

links = ""
for css in css_files:
    links += f'<link rel="stylesheet" href="/assets/{os.path.basename(css)}">\n'

scripts = ""
for js in js_files:
    scripts += f'<script type="module" src="/assets/{os.path.basename(js)}"></script>\n'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TeamStandup</title>
  {links}
</head>
<body>
  <div id="root"></div>
  {scripts}
</body>
</html>
"""

output_path = os.path.join(client_dir, "index.html")
with open(output_path, "w") as f:
    f.write(html)
print(f"Generated {output_path}")
