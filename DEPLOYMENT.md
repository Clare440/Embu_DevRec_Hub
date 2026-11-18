# Deploying to PythonAnywhere (free tier) and testing it live

## A. Upload
1. Create a free account at pythonanywhere.com → **Files** tab → make folder `embu_devrec_hub`.
2. Upload `app.py`, `requirements.txt`, `test_app.py`, and the `templates/` + `static/css/` folders (keep the same structure).
   Do NOT upload your old `api_records.db` (it has an old table called `communications`, which doesn't match the app).

## B. Install & test in the cloud console
Open **Consoles → Bash**:
```
cd ~/embu_devrec_hub
python3 -m venv ~/venv && source ~/venv/bin/activate
pip install -r requirements.txt
python test_app.py
```
Expect `Ran 11 tests ... OK`. Screenshot this: it is your "tests in the deployment environment" evidence.

## C. Create the web app
1. **Web** tab → *Add a new web app* → **Manual configuration** → pick the Python version you used for the venv.
2. *Virtualenv* box: `/home/<yourusername>/venv`
3. *Source code*: `/home/<yourusername>/embu_devrec_hub`
4. Click the **WSGI configuration file** link, delete everything, paste:
```
import sys, os
path = '/home/<yourusername>/embu_devrec_hub'
if path not in sys.path: sys.path.insert(0, path)
os.environ['SECRET_KEY'] = 'put-a-long-random-string-here'
os.environ['HMAC_SECRET'] = 'put-another-long-random-string-here'
os.environ['DATABASE_URL'] = 'sqlite:////home/<yourusername>/embu_devrec_hub/api_records.db'
from app import app as application
```
5. Press the green **Reload** button. Visit `https://<yourusername>.pythonanywhere.com`.
   If you get an error, open the **Error log** link on the Web tab.

## D. Live checklist (do this on the deployed URL, screenshot each step)
| # | Pillar | Do this | Expected |
|---|--------|---------|----------|
| 7 | Security | Open `/search` while logged out | Redirected to login |
| 7 | Security | Login with wrong password, then `clare` / `Admin2026!` | Error, then dashboard |
| 3 | Insert | Add Equity Bank, `/api/v1/payments`, `{"amount": 1000}` | Success message, row appears |
| 6 | Uniqueness | Add the exact same record again | DUPLICATE ERROR |
| 1 | Search | Search `equity`, then `payments`, then the first 8 chars of a hash | Row filters correctly |
| 2 | Update | Edit the payload, save | Hash in table changes, still VERIFIED |
| 5 | Integrity | Bash console: `sqlite3 api_records.db "update api_record set request_payload='{\"amount\":999}' where id=1;"` then refresh | Row shows TAMPERED, dashboard count drops |
| 4 | Delete | Delete a record | Removed; Dashboard audit trail shows DELETE |

(For step 5, if the `sqlite3` command isn't found use: `python -c "import sqlite3;c=sqlite3.connect('api_records.db');c.execute(\"update api_record set request_payload='x' where id=1\");c.commit()"`)

## E. Before the final presentation
- Change the default password (`Admin2026!`) and remove the "Default: clare / ..." hint if you show a login page.
- Never run with `debug=True` online (the app now only does so if `FLASK_DEBUG=1`).
- Free PythonAnywhere apps must be re-extended every ~3 months; reload the site the morning of your demo.
