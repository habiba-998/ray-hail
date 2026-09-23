# Deploying RAY to Streamlit Community Cloud

Result: a public HTTPS URL (`https://<your-app>.streamlit.app`) that works on any phone, tablet or laptop,
with **real Google Earth Engine data** and without your computer running.

> 🔐 **Security rules**
> - The service-account key is stored **only** in Streamlit Secrets (encrypted by the platform).
> - Never put the key file inside this folder, never commit it, never paste it into the source code.
> - `.gitignore` excludes `.streamlit/secrets.toml` and common key-file names, but the safest rule is to keep
>   the downloaded key **outside** the project folder (and outside OneDrive).
> - If a key is ever exposed: Google Cloud Console → IAM & Admin → Service Accounts → *your account* → Keys →
>   delete it, then create a new one and update the secret.

---

## 1 · Service account for Earth Engine (Google Cloud Console, ~10 min)

Project: **`ray-hail-2026`** (already registered for Earth Engine, API enabled).

1. Open <https://console.cloud.google.com/iam-admin/serviceaccounts?project=ray-hail-2026>
2. **Create service account** → name `ray-streamlit` → *Create and continue*.
3. Grant roles:
   - **Earth Engine Resource Viewer** (`roles/earthengine.viewer`)
   - **Service Usage Consumer** (`roles/serviceusage.serviceUsageConsumer`)

   → *Continue* → *Done*.
4. Open the new account → **Keys** → **Add key** → **Create new key** → **JSON** → the file downloads.
   Move it to a private folder **outside** the RAY project and outside OneDrive (e.g. `C:\keys\`).
5. Print the ready-to-paste secrets block (runs locally, only prints to your terminal):

   ```bash
   .venv\Scripts\python.exe tools\key_to_secrets.py "C:\keys\ray-streamlit-key.json" ray-hail-2026
   ```

   Keep the terminal open for step 3.

If step 4 says key creation is disabled by an organisation policy, stop and use the Cloud Run alternative
(service identity without keys) instead.

## 2 · Public GitHub repository (~5 min)

1. On <https://github.com/new> create a **public**, **empty** repository (no README / .gitignore / licence),
   e.g. `ray-hail`.
2. Push this folder (the first commit was prepared and checked for secrets):

   ```bash
   git remote add origin https://github.com/<your-user>/ray-hail.git
   git push -u origin main
   ```

   Git for Windows opens a browser window for the GitHub sign-in.

## 3 · Streamlit Community Cloud (~5 min)

1. <https://share.streamlit.io> → sign in with GitHub → **Create app** → *Deploy a public app from GitHub*.
2. Repository `<your-user>/ray-hail`, branch `main`, main file **`app.py`**, pick an app URL (e.g. `ray-hail`).
3. **Advanced settings** → Python **3.12** → **Secrets**: paste the block printed in step 1.5.
4. **Deploy**. The first build installs the pinned `requirements.txt` (a few minutes).

## 4 · Verify, then submit the URL

Open the URL on your phone:

- [ ] Green badge **"Google Earth Engine — Real Satellite Data · Sentinel-2 image of …"**
- [ ] Farmer mode: Farm Status, Today's Priority, map with coloured zones, tap a zone, View details
- [ ] العربية / English switch
- [ ] Technical mode: Satellite Map layers, Analytics, AI & Method (Random Forest shows NOT TRAINED)
- [ ] Sidebar (») → Data source → Demo mode shows the yellow **DEMO DATA** badge

The first real-data load after a restart takes roughly 30–60 s; afterwards results are cached for an hour.

## Operating notes

- **Latest image by default.** The app always opens on the newest Sentinel-2 acquisition over the farm that is at
  least 50 % cloud-free. Results change as new images arrive; the date selector (sidebar) shows earlier dates.
- **Sleep.** Community Cloud puts apps to sleep after a period without visitors. A reviewer then sees a *wake up*
  button and waits about a minute. Open the URL yourself shortly before review windows.
- **Quota.** Visitors use the Earth Engine quota of `ray-hail-2026` (noncommercial projects have a monthly compute
  quota). Check it under Google Cloud Console → Earth Engine → Quota.
- **Project field is locked** on the deployment (service account configured) so that no visitor can re-point the
  shared Earth Engine connection.
- **Updating the app:** commit and `git push`; Community Cloud redeploys automatically.
