import os

basedir = os.path.abspath(os.path.dirname(__file__))
static_dir = os.path.join(basedir, 'static')
js_dir = os.path.join(static_dir, 'js')
login_js = os.path.join(js_dir, 'login.js')

print(f"Checking for file at: {login_js}")

if os.path.exists(login_js):
    print("✅ SUCCESS: The file exists.")
else:
    print("❌ FAILURE: The file is missing.")
    print(f"Contents of {static_dir}:")
    if os.path.exists(static_dir):
        print(os.listdir(static_dir))
        if os.path.exists(js_dir):
            print(f"Contents of {js_dir}: {os.listdir(js_dir)}")