# PCTS - Manual Run Instructions

## Prerequisites

1. **Python 3.8+** installed
2. **MySQL Server** running (version 5.7+ or 8.0+)
3. **MongoDB** running (version 4.0+)

## Setup Steps

### 1. Activate Virtual Environment

```powershell
cd "d:\Parcel And Courier Tracking System"
.\venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

If you see errors about uvicorn, install it explicitly:
```powershell
pip install uvicorn
```

### 3. Configure Environment Variables

Edit the `.env` file with your database credentials:

```
# MySQL Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=pcts_db

# MongoDB Configuration  
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=pcts_logs

# JWT Secret (change this in production!)
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 4. Setup MySQL Database

Run these SQL scripts in order using MySQL Workbench or command line:

```sql
-- 1. Create database and tables
SOURCE sql/01_create_tables.sql;

-- 2. Insert sample data
SOURCE sql/02_sample_data.sql;

-- 3. Create indexes for performance
SOURCE sql/05_indexes.sql;

-- 4. Create stored procedures
SOURCE sql/procedures.sql;
```

Or via command line:
```powershell
mysql -u root -p < sql/01_create_tables.sql
mysql -u root -p < sql/02_sample_data.sql
mysql -u root -p < sql/05_indexes.sql
mysql -u root -p < sql/procedures.sql
```

### 5. Start the Backend Server

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 6. Open the Application

Navigate to: **http://127.0.0.1:8000/static/login.html**

## Demo Credentials

### Customer Account
- **Email**: arun.kumar@gmail.com
- **Password**: Customer@12345
- **Features**: Book parcels, track shipments, view history

### Admin Account
- **Email**: admin@pcts.com
- **Password**: Admin@12345
- **Features**: Full system access, assign agents, manage payments, view reports

### Delivery Agent Account
- **Email**: ravi.delivery@pcts.com
- **Password**: Delivery@12345
- **Features**: View assigned parcels, update delivery status, mark deliveries

## Testing the Complete Workflow

### Test Scenario 1: Book and Assign Parcel

1. **Login as Customer** (arun.kumar@gmail.com)
2. Click **"Book Parcel"**
3. Fill in sender/receiver details
4. Click **"Calculate Charge"** to see pricing
5. Submit the booking
6. **Logout** and login as **Admin**
7. Go to **Dashboard**
8. Find the newly booked parcel
9. Click **"Assign Agent"** button
10. Select a delivery agent from dropdown
11. Submit assignment
12. **Verify**: Button changes to "✓ Assigned" badge (GREEN)
13. **Verify**: Table auto-refreshes with updated data

### Test Scenario 2: Update Payment Status

1. **Login as Admin** (admin@pcts.com)
2. Go to **Dashboard**
3. Find a parcel with **PENDING** payment status
4. Click **"Update"** button next to payment badge
5. In the modal:
   - Select **Payment Status**: Paid
   - Select **Payment Method**: UPI (or any method)
   - Enter **Amount** (should match parcel charge)
   - Add optional notes
6. Click **"Update Payment"**
7. **Verify**: Payment badge changes to "PAID" (GREEN)
8. **Verify**: Update button disappears for paid parcels

### Test Scenario 3: Delivery Agent Workflow

1. **Logout** and login as **Delivery Agent** (ravi.delivery@pcts.com)
2. Go to **Delivery Dashboard**
3. View parcels assigned to you
4. Click **"Update Status"** on a parcel
5. Change status from **In Transit** → **Out for Delivery**
6. Add location/notes
7. Submit
8. **Later**: Change to **Delivered** status
9. **Verify**: Status updates reflected in customer tracking page

### Test Scenario 4: Customer Tracking

1. **Login as Customer**
2. Go to **Track Parcel** page
3. Enter tracking ID (e.g., TRK001, TRK002)
4. Click **Track**
5. **Verify**: 
   - Status timeline shows correctly
   - Location updates display
   - Payment status visible
   - ETA shown if available

## Common Issues and Fixes

### Issue 1: "Unable to create process using venv/Scripts/python.exe"

**Fix:**
```powershell
pip install uvicorn
python -m uvicorn backend.main:app --reload --port 8000
```

### Issue 2: Database Connection Error

**Fix:**
- Verify MySQL is running
- Check `.env` file has correct credentials
- Test connection: `mysql -u root -p`

### Issue 3: MongoDB Connection Error

**Fix:**
- Verify MongoDB is running
- Check MongoDB service: `net start MongoDB`
- Or start manually: `mongod --dbpath="C:\data\db"`

### Issue 4: Port 8000 Already in Use

**Fix:**
```powershell
# Use a different port
python -m uvicorn backend.main:app --reload --port 8001

# Or find and kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

### Issue 5: Static Files Not Loading (CSS/JS)

**Fix:**
- Ensure you're accessing via `http://127.0.0.1:8000/static/login.html`
- NOT via file:// protocol
- Check browser console for errors (F12)

## API Documentation

Once the server is running, access interactive API docs at:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Stopping the Server

Press **CTRL+C** in the terminal where uvicorn is running.

## Project Structure

```
Parcel And Courier Tracking System/
├── backend/
│   ├── main.py              # FastAPI application entry
│   ├── database.py          # MySQL connection
│   ├── mongo.py             # MongoDB connection
│   ├── security.py          # Authentication/JWT
│   ├── models/              # SQLAlchemy ORM models
│   ├── routers/             # API endpoints
│   └── schemas/             # Pydantic validation
├── frontend/
│   ├── *.html               # HTML pages
│   ├── css/style.css        # Styling
│   └── js/                  # JavaScript modules
├── sql/                     # Database scripts
├── .env                     # Environment config
└── requirements.txt         # Python dependencies
```

## Need Help?

Check the following files:
- **architecture.md** - System architecture overview
- **databaseDesign.md** - Database schema details
- **edge_case.md** - Business rules and edge cases
- **FINAL_BUG_FIXES.md** - All bugs fixed in this version

## Success Indicators

✅ Server starts without errors  
✅ Can login with all three user roles  
✅ Can book a parcel as customer  
✅ Admin can assign parcel to agent (button → badge)  
✅ Admin can update payment status  
✅ Delivery agent can update delivery status  
✅ Customer can track parcel with timeline  
✅ All status badges display correctly  
✅ Payment management fully functional
