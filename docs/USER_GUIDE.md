# ColdGuard User Guide
**For ANMs, Cold Chain Officers, and PHC Staff**

---

## What is ColdGuard?

ColdGuard is a tool that tells you whether a vaccine is still safe to use after a temperature alarm or power outage. Instead of just saying "the temperature went above 8°C — discard," ColdGuard calculates exactly how much potency the vaccine lost, and gives you a clear recommendation.

---

## Step 1: Open ColdGuard

**Web App:**
```
http://your-server/coldguard
```
or run locally: `streamlit run web_app/app.py`

**Mobile App:** Open the ColdGuard app on your Android phone.

---

## Step 2: Select Your Vaccine

From the dropdown menu, choose the vaccine type:
- DPT (Diphtheria-Pertussis-Tetanus)
- OPV (Oral Polio Vaccine)
- MMR / Measles
- BCG
- Hepatitis B
- IPV (Inactivated Polio Vaccine)
- Rotavirus
- PCV (Pneumococcal Conjugate Vaccine)

---

## Step 3: Enter the Temperature Log

**Option A: Upload a CSV file**
If your cold chain logger (Berlinger Fridge-tag, etc.) can export data, download the CSV and upload it. The file must have two columns: `timestamp` and `temperature_celsius`.

**Option B: Manual Entry**
Enter each temperature reading with its date and time. Add as many rows as you have readings. Example:

| Timestamp | Temperature |
|-----------|-------------|
| 2024-09-01 08:00 | 4.2°C |
| 2024-09-01 14:00 | 14.3°C |
| 2024-09-01 20:00 | 4.1°C |

---

## Step 4: Click "Analyze"

ColdGuard will compute the result in 1–2 seconds.

---

## Step 5: Read the Result

### The Decision Banner

A large colored banner shows one of three decisions:

🟢 **USE** — The vaccine retains sufficient potency. It is safe to administer.

🟡 **INVESTIGATE** — Uncertainty is high. Contact your district cold chain officer before using.

🔴 **DISCARD** — Estimated potency is likely below the minimum threshold. Do not administer.

### The Potency Estimate

A percentage and confidence interval are shown. For example:
> **97.8% potency (90% confidence interval: 94–99%)**

This means: ColdGuard estimates the vaccine is at 97.8% of its original potency. We are 90% confident the true potency is between 94% and 99%.

### The Explanation

A plain-language sentence explains what happened. For example:
> *"Primary heat exposure: 11.0 hours at 14.3°C caused 2% of total potency loss. Potency remains above 80% minimum with 98% confidence. This vaccine is safe to administer."*

### Degradation Breakdown

Expand the "Degradation Breakdown" section to see which time periods caused the most potency loss.

---

## Freeze-Sensitive Vaccines

DPT, Hepatitis B, IPV, and PCV are damaged by freezing. If the temperature log shows readings below 0°C, ColdGuard will display a **FREEZE WARNING**. Contact your supervisor if a freeze event is detected for these vaccines.

---

## Downloading the Report

Click **Download PDF Report** to save a record of the analysis. Keep this for your audit log.

---

## Frequently Asked Questions

**Q: The VVM shows a color change. Does that mean I should discard?**
A: Not necessarily. Run ColdGuard with the full temperature log. The VVM is calibrated conservatively. ColdGuard may show the vaccine is still above the potency threshold.

**Q: What if my logger has a gap in readings?**
A: ColdGuard will warn you about unmonitored periods. This increases uncertainty but does not automatically mean the vaccine should be discarded.

**Q: Can ColdGuard work without internet?**
A: Yes. The mobile app works entirely offline. The web app also works offline when run locally.

**Q: Who should I contact with questions?**
A: Contact your District Cold Chain Officer. Show them the ColdGuard report.

---

## Important Notice

ColdGuard provides decision support based on published pharmaceutical kinetic models. It does not replace clinical judgment. In cases of doubt (INVESTIGATE result), always consult your district cold chain officer before administering vaccines.
