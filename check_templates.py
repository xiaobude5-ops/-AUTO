import sys, os
sys.path.insert(0, r'D:\YIONpro\几何星球AUTO')
os.chdir(r'D:\YIONpro\几何星球AUTO')

from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')

with app.app_context():
    html = render_template('dashboard.html')
    ok = 'video-link' in html
    col9 = 'colspan="9"' in html
    print('video-link:', ok)
    print('colspan=9:', col9)

    html2 = render_template('admin.html')
    print('admin video-link:', 'video-link' in html2)
    print('admin colspan=12:', 'colspan="12"' in html2)
