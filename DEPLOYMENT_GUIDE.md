# PCTS Deployment Guide — Complete Step-by-Step Instructions

This guide provides **4 practical methods** to deploy the **Parcel and Courier Tracking System (PCTS)**, ranging from instant 1-minute live internet tunnels to permanent free cloud hosting.

---

## Method 1: Instant Live Public HTTPS Link via Ngrok / Cloudflare Tunnel
*(**Best for College Review / Practical Exam Demo** — Takes 2 minutes, requires ZERO database migration, and works with your existing local MySQL & MongoDB!)*

With this method, your laptop runs the server and databases, while an encrypted tunnel provides a live public `https://...` link that anyone (including your Sir or external examiner) can open on their phone or laptop.

### Steps:
1. **Start your local PCTS server:**
   ```powershell
   cd "D:\Parcel And Courier Tracking System"
   .\venv\Scripts\activate
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

2. **Option A — Using Free Cloudflare Tunnel (No account needed):**
   - Download the free `cloudflared.exe` from [https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).
   - Open a second terminal window and run:
     ```powershell
     cloudflared tunnel --url http://127.0.0.1:8000
     ```
   - Cloudflare will generate a public URL like:
     `https://random-name-subdomain.trycloudflare.com`
   - Share this link! It opens your live website with full tracking, login, and database functionality.

3. **Option B — Using Ngrok:**
   - Download Ngrok from [ngrok.com](https://ngrok.com) and run:
     ```powershell
     ngrok http 8000
     ```
   - Copy the `Forwarding` URL (e.g., `https://xxxx.ngrok-free.app`).

---

## Method 2: Permanent Free Cloud Deployment on Render
*(**Best for 24/7 Cloud Hosting** — Runs on the cloud even when your laptop is turned off!)*

### Step 1: Set Up Free Cloud MySQL
Choose any free cloud MySQL provider:
- **Aiven for MySQL (Recommended):** [https://aiven.io/mysql](https://aiven.io/mysql) (Free 5GB tier, forever free).
  - Create an account $\rightarrow$ Create Service $\rightarrow$ Select **MySQL (Free)**.
  - Copy the **Service URI** (e.g. `mysql://avnadmin:password@mysql-xxxxx.aivencloud.com:12345/defaultdb?ssl-mode=REQUIRED`).
  - Open MySQL Workbench or run your SQL setup script (`sql/01_create_tables.sql`, `sql/procedures.sql`, `sql/02_sample_data.sql`, `sql/05_indexes.sql`) against this remote database.

- **Alternative:** **TiDB Cloud (Serverless MySQL Compatible):** [https://tidbcloud.com](https://tidbcloud.com) (Free 5GB tier).

---

### Step 2: Push Your Code to GitHub
1. In your project directory:
   ```powershell
   git add .
   git commit -m "Add deployment configuration files"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/pcts-logistics.git
   git push -u origin main
   ```

---

### Step 3: Deploy on Render.com
1. Go to **[https://render.com](https://render.com)** and sign in with GitHub.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select your repository: `pcts-logistics`.
4. Configure settings:
   - **Name:** `pcts-tracking`
   - **Region:** Singapore or Frankfurt (fastest for India)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
5. Click **Advanced** $\rightarrow$ **Add Environment Variable**:
   - `DATABASE_URL`: *(Paste your cloud MySQL URI from Step 1, using driver `mysql+pymysql://...`)*
   - `JWT_SECRET_KEY`: `pcts_super_secure_jwt_secret_key_college_project_2026`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `120`
6. Click **Create Web Service**.
7. Render will build and deploy your app. Within 2–3 minutes, you will get a permanent live URL:
   `https://pcts-tracking.onrender.com`

---

## Method 3: Local Network (LAN / Wi-Fi) Deployment
*(**Best for Practical Exam Hall / Classroom Demo** — No internet required! Works over local Wi-Fi / Hotspot!)*

If your college lab has strict firewall restrictions or slow internet, you can broadcast the website directly across the lab's Wi-Fi network or your mobile hotspot.

### Steps:
1. **Connect your laptop and the examiner/phone to the same Wi-Fi or mobile hotspot.**
2. **Find your laptop's local IPv4 Address:**
   - Open PowerShell and type:
     ```powershell
     ipconfig
     ```
   - Look for **IPv4 Address** under your active Wi-Fi adapter (e.g., `192.168.1.45` or `192.168.43.120`).
3. **Start PCTS listening on all interfaces (`0.0.0.0`):**
   ```powershell
   cd "D:\Parcel And Courier Tracking System"
   .\venv\Scripts\activate
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
4. **Allow through Windows Firewall (One-Time Prompt):**
   - If Windows Firewall asks to allow Python through private networks, click **Allow Access**.
5. **Open on any phone, tablet, or external laptop:**
   - In any browser on any connected device, open:
     `http://192.168.1.45:8000` *(replace with your actual IPv4 address)*
   - The full website (Customer, Admin, and Delivery portals) will load live on their device!

---

## Method 4: Docker Container Deployment
*(**Best for Modern DevOps Showcase**)*

You already have the production-ready `Dockerfile` in the project root:

1. **Build the Docker container image:**
   ```powershell
   docker build -t pcts-app:v1 .
   ```

2. **Run the container:**
   ```powershell
   docker run -d -p 8000:8000 --name pcts-server --env-file .env pcts-app:v1
   ```

3. **Check status:**
   ```powershell
   docker ps
   curl http://localhost:8000/health
   ```

---

## Demo Accounts Quick Reference for Evaluation

| Role | Email | Password | Access Portal |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@pcts.com` | `Admin@12345` | `dashboard.html` & `admin_fleet.html` |
| **Delivery Agent** | `ravi.delivery@pcts.com` | `Delivery@12345` | `delivery_dashboard.html` |
| **Customer** | `arun.kumar@gmail.com` | `Customer@12345` | `customer_dashboard.html` & `book.html` |
