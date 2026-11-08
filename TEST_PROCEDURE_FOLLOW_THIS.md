# ✅ EXACT TEST PROCEDURE - FOLLOW STEP BY STEP

**YOUR SERVER IS RUNNING!** I just tested it - working perfectly.

---

## 🎯 PART 1: OPEN THE WEBSITE (30 seconds)

### Step 1.1: Open Your Web Browser

- Click the **Chrome** icon (or Edge/Firefox)
- A blank browser window opens

### Step 1.2: Type This URL EXACTLY

Click in the address bar at the top and type (or copy-paste):

```
http://127.0.0.1:8000/static/login.html
```

Press **Enter**

### Step 1.3: What You Should See

A login page with:
- **PCTS Express** logo/title at top
- Email input box
- Password input box  
- Blue "Login" button
- "Don't have an account? Register" link

**✅ If you see this → Continue to Part 2**

**❌ If you DON'T see this:**
- Take a screenshot (Windows + Shift + S)
- Tell me what you see instead
- Show me any error message

---

## 🎯 PART 2: LOGIN AS ADMIN (1 minute)

### Step 2.1: Enter Email

Click in the **Email** box and type EXACTLY (or copy-paste):

```
admin@pcts.com
```

**Important:** 
- Small letters 'a' in admin
- Small letters 'pcts'  
- No spaces before or after

### Step 2.2: Enter Password

Click in the **Password** box and type EXACTLY (or copy-paste):

```
Admin@12345
```

**Important:**
- Capital 'A' in Admin
- @ symbol
- Numbers 12345
- No spaces

### Step 2.3: Click Login Button

Click the blue **"Login"** button

### Step 2.4: What You Should See

After login, you should see a new page with:
- Navigation bar at top (Dashboard, Track, Book Parcel, etc.)
- Your name/role in top right: "Logged as: Admin (HQ)"
- Statistics cards showing numbers
- A big table with parcel data

**✅ If you see the dashboard → Continue to Part 3**

**❌ If login fails:**
- Check you typed email and password EXACTLY as shown
- No extra spaces
- Check capital A in Admin@12345
- Try copy-pasting the credentials again

---

## 🎯 PART 3: TEST ASSIGNMENT FEATURE (2 minutes)

### Step 3.1: Look at the Table

You should see a table with columns:
- Tracking ID
- Sender
- Receiver
- Route
- Weight
- Status
- Payment
- Assigned Agent
- **Action** (last column on the right)

### Step 3.2: Find an "Assign Agent" Button

Scroll through the table and look at the **last column (Action)**.

Find a row that has a **blue button** saying **"Assign Agent"**

**What it looks like:**
```
┌───────────────────┐
│  Assign Agent     │  ← Blue button
└───────────────────┘
```

**Note:** Some rows might show:
- "✓ Assigned" badge → Skip this (already assigned)
- "View Logs" button → Skip this (completed delivery)

**Find one that says "Assign Agent"**

### Step 3.3: Click "Assign Agent"

Click the blue **"Assign Agent"** button

### Step 3.4: What Happens

A popup window (modal) appears in the center of the screen:

```
┌─────────────────────────────────────┐
│ Assign Delivery Agent            × │
├─────────────────────────────────────┤
│                                     │
│ Parcel Tracking ID:                 │
│ [TRK12345]  ← Shows the tracking ID │
│                                     │
│ Select Available Agent:             │
│ [Choose a delivery executive ▼]     │
│                                     │
│ Assignment Instructions (Optional): │
│ [                            ]      │
│                                     │
│ [Cancel] [Confirm Assignment]       │
└─────────────────────────────────────┘
```

### Step 3.5: Select a Delivery Agent

Click on the **dropdown** that says "Choose a delivery executive"

You'll see a list of agents like:
- Ravi Kumar (Mumbai Central - Bike)
- Suresh Patil (Pune Zone - Van)
- Anjali Rao (Bengaluru South - EV Scooter)
- etc.

**Click on ANY agent name** (doesn't matter which one)

### Step 3.6: Click "Confirm Assignment"

Click the blue **"Confirm Assignment"** button at the bottom

### Step 3.7: What You Should See (THE IMPORTANT PART!)

**IMMEDIATELY after clicking:**

1. A popup alert appears saying:
   ```
   Parcel TRK12345 successfully assigned to delivery executive!
   ```

2. Click **OK** on this alert

3. **THE MODAL CLOSES BY ITSELF** (you don't need to close it)

4. **THE TABLE REFRESHES BY ITSELF** (you don't need to press F5)

5. **LOOK AT THE SAME ROW WHERE YOU CLICKED:**

   **BEFORE:** 
   ```
   │ Action              │
   │ [Assign Agent]      │  ← Was a blue button
   ```

   **AFTER (THE FIX):**
   ```
   │ Action          │
   │ ✓ Assigned      │  ← Now a GREEN badge!
   ```

**✅ THIS IS THE FIX!** The button should change to a green badge!

**If the button is STILL there:**
1. Wait 2 seconds
2. Look at the "Assigned Agent" column - does it show an agent name?
3. If yes, click the "🔄 Refresh" button in the dashboard (top right)
4. The badge should appear

### Step 3.8: Take a Screenshot

**Important for your supervisor:**
- Take a screenshot showing the green "✓ Assigned" badge
- Windows + Shift + S to capture
- This proves the feature is working

---

## 🎯 PART 4: TEST PAYMENT FEATURE (2 minutes)

### Step 4.1: Find a "PENDING" Payment

Look at the **"Payment"** column in the table (7th column from left)

Find a row that shows:
```
│ Payment               │
│ [PENDING]  [Update]   │  ← Yellow badge + Update button
```

**Colors to look for:**
- **YELLOW badge** = PENDING
- **Small "Update" button** next to it

**Note:** If you see:
- GREEN "PAID" badge → No Update button (can't update paid payments)
- Look for PENDING ones

### Step 4.2: Click "Update" Button

Click the small **"Update"** button next to the PENDING badge

### Step 4.3: What Happens (THE NEW FEATURE!)

A **NEW POPUP MODAL** appears (this was completely missing before!):

```
┌──────────────────────────────────────┐
│ Update Payment Information        × │
├──────────────────────────────────────┤
│                                      │
│ Parcel Tracking ID:                  │
│ [TRK12345]  ← Shows tracking ID      │
│                                      │
│ Payment Amount (₹):                  │
│ [450.00]  ← Shows charge amount      │
│                                      │
│ Payment Status:                      │
│ [Pending ▼]  ← Dropdown              │
│                                      │
│ Payment Method:                      │
│ [Cash ▼]  ← Dropdown                 │
│                                      │
│ Transaction Notes (Optional):        │
│ [                              ]     │
│                                      │
│ [Cancel]  [Update Payment]           │
└──────────────────────────────────────┘
```

**✅ If this modal appears → Great! This is the new feature!**

**❌ If nothing happens:**
- Press F12 key
- Click "Console" tab
- Take screenshot of any red errors
- Show me

### Step 4.4: Change Payment Status

Click on the **"Payment Status"** dropdown (currently shows "Pending")

A dropdown list appears:
- Pending
- Paid
- Failed

**Click on "Paid"**

### Step 4.5: Change Payment Method

Click on the **"Payment Method"** dropdown (currently shows "Cash")

A dropdown list appears:
- Cash on Delivery
- Credit/Debit Card
- UPI
- Net Banking
- Digital Wallet

**Click on "UPI"** (or any method you like)

### Step 4.6: Optional - Add Note

You can type something in "Transaction Notes" like:
```
Test payment update
```

This is optional - you can leave it blank.

### Step 4.7: Click "Update Payment"

Click the blue **"Update Payment"** button at the bottom

### Step 4.8: What You Should See (THE IMPORTANT PART!)

**IMMEDIATELY after clicking:**

1. A popup alert appears saying:
   ```
   Payment for TRK12345 updated successfully!
   ```

2. Click **OK** on this alert

3. **THE MODAL CLOSES BY ITSELF**

4. **THE TABLE REFRESHES BY ITSELF**

5. **LOOK AT THE SAME ROW IN THE PAYMENT COLUMN:**

   **BEFORE:**
   ```
   │ Payment               │
   │ [PENDING]  [Update]   │  ← Yellow badge + button
   ```

   **AFTER (THE FIX):**
   ```
   │ Payment    │
   │ [PAID]     │  ← GREEN badge, NO button!
   ```

**✅ THIS IS THE FIX!** 
- Badge changes from YELLOW to GREEN
- "Update" button DISAPPEARS (can't update paid payments)

### Step 4.9: Take a Screenshot

**Important for your supervisor:**
- Take a screenshot showing:
  - The green "PAID" badge
  - No "Update" button next to it
- This proves the payment feature is working

---

## 🎯 PART 5: COMPLETE TEST (Optional - 5 minutes)

If you want to test the FULL workflow:

### Book a Parcel as Customer

1. Click "Sign Out" button (top right)
2. Login as Customer:
   ```
   Email: arun.kumar@gmail.com
   Password: Customer@12345
   ```
3. Click "Book Parcel"
4. Fill the form:
   - Category: Document
   - Weight: 2
   - Description: Test parcel
   - Sender Name: Test Sender
   - Sender Phone: 9876543210
   - Sender Address: Test Address 1
   - Receiver Name: Test Receiver
   - Receiver Phone: 9876543211
   - Receiver Address: Test Address 2
   - Source City: Mumbai
   - Destination City: Delhi
5. Click "Calculate Charge" (you'll see the price)
6. Click "Book Parcel"
7. **Note down the Tracking ID** (like TRK00075)

### Assign as Admin

8. Logout, login as Admin (admin@pcts.com / Admin@12345)
9. Go to Dashboard
10. In search box, type your tracking ID
11. Find your parcel
12. Click "Assign Agent"
13. Select agent, confirm
14. ✅ Verify: Button → "✓ Assigned" badge

### Update Payment as Admin

15. Same parcel, click "Update" next to PENDING
16. Change to "Paid", method "UPI"
17. Click "Update Payment"
18. ✅ Verify: Badge → "PAID", button disappears

### Update Status as Delivery Agent

19. Logout, login as Delivery Agent (ravi.delivery@pcts.com / Delivery@12345)
20. Go to "Delivery Dashboard"
21. Find your assigned parcel
22. Click "Update Status"
23. Change to "In Transit", location "Mumbai Hub"
24. Update again to "Out for Delivery"
25. Final update to "Delivered"

### Track as Customer

26. Logout, login as Customer (arun.kumar@gmail.com / Customer@12345)
27. Click "Track Parcel"
28. Enter your tracking ID
29. Click "Track"
30. ✅ Verify: Timeline shows all updates, status "Delivered", payment "PAID"

---

## ❓ TROUBLESHOOTING

### Problem: Page doesn't load

**Check:**
1. Look for the PowerShell window where I started the server
2. Should say "Uvicorn running on http://127.0.0.1:8000"
3. If window is closed, server stopped

**Fix:**
```
Tell me "server stopped" and I'll restart it
```

### Problem: Can't login

**Fix:**
Copy-paste these EXACTLY:
```
Email: admin@pcts.com
Password: Admin@12345
```
Note the capital A in Admin!

### Problem: Table is empty

**Fix:**
- Click the "🔄 Refresh" button in dashboard (top right)
- Or press F5 to reload page
- Database might need re-initialization

### Problem: Button doesn't change after assignment

**Check:**
1. Did you see success alert?
2. Did alert say "successfully assigned"?
3. Wait 2 seconds

**Fix:**
- Click "🔄 Refresh" button
- Check "Assigned Agent" column - does it show a name?
- If yes, the assignment worked (badge should appear after refresh)

### Problem: Payment modal doesn't open

**Check:**
1. Are you clicking on PENDING payment? (yellow badge)
2. PAID payments don't have Update button

**If PENDING but modal doesn't open:**
1. Press F12 key
2. Click "Console" tab at top
3. Take screenshot of red errors
4. Send to me

### Problem: Changes not saving

**Check server logs:**
1. Look at the PowerShell terminal
2. After clicking Update, check for red ERROR messages
3. Take screenshot and show me

---

## 📸 SCREENSHOTS TO TAKE

For your supervisor, take these screenshots:

1. **Login page** - showing it loads
2. **Admin dashboard** - showing table with parcels
3. **Assignment modal** - showing the assign agent popup
4. **After assignment** - showing green "✓ Assigned" badge
5. **Payment modal** - showing the payment update popup
6. **After payment update** - showing green "PAID" badge
7. **Complete timeline** - tracking page showing full journey

---

## ✅ SUCCESS CHECKLIST

Check each item as you test:

**Basic Access:**
- [ ] Can open http://127.0.0.1:8000/static/login.html
- [ ] Login page loads correctly
- [ ] Can login as admin@pcts.com / Admin@12345
- [ ] Dashboard loads with table

**Assignment Feature (Bug Fix #1):**
- [ ] Can see "Assign Agent" buttons in table
- [ ] Click button → modal opens
- [ ] Select agent → click confirm
- [ ] See success alert
- [ ] **Button changes to "✓ Assigned" badge (GREEN)** ⭐
- [ ] Badge appears immediately without manual refresh ⭐

**Payment Feature (Bug Fix #2):**
- [ ] Can see PENDING payments with "Update" button
- [ ] Click "Update" → **modal opens** ⭐
- [ ] **Modal has all fields (status, method, notes)** ⭐
- [ ] Change status to "Paid", method to "UPI"
- [ ] Click "Update Payment"
- [ ] See success alert
- [ ] **Badge changes to "PAID" (GREEN)** ⭐
- [ ] **"Update" button disappears** ⭐

**All items checked?** 🎉 **Both features working!**

---

## 🚨 IF STILL NOT WORKING

Tell me EXACTLY:

1. **Which step you're on** (e.g., "Part 3, Step 3.3")
2. **What you did** (e.g., "Clicked Assign Agent button")
3. **What happened** (e.g., "Nothing happened" or "Error message appeared")
4. **Screenshot** of:
   - The page you're on
   - Browser console (F12 → Console tab)
   - Server terminal (PowerShell window)

I will fix it immediately!

---

## 🎉 YOU'RE READY!

Follow this document step by step. If anything doesn't work EXACTLY as described, stop and tell me which step failed.

**Server is running RIGHT NOW. Start from Part 1!** 🚀
