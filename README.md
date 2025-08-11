# Wembley-stadium-event-calendar

[![Latest Tag](https://img.shields.io/github/v/tag/Paxton-W/Wembley-stadium-event-calendar?label=version)](https://github.com/Paxton-W/Wembley-stadium-event-calendar/tags)
[![Scheduled Calendar Build](https://github.com/Paxton-W/Wembley-stadium-event-calendar/actions/workflows/build.yml/badge.svg)](https://github.com/Paxton-W/Wembley-stadium-event-calendar/actions/workflows/build.yml)
[![ICS Last Updated](https://img.shields.io/endpoint?url=https%3A%2F%2Fshieldsio-ics-date.vercel.app%2Fapi%2FPaxton-W%2FWembley-stadium-event-calendar%2Fdocs%2Fcalendar.ics&label=last%20updated)](https://Paxton-W.github.io/Wembley-stadium-event-calendar/calendar.ics)
[![Subscribe iOS/macOS](https://img.shields.io/badge/Subscribe-Apple%20Calendar-blue?logo=apple)](webcal://Paxton-W.github.io/Wembley-stadium-event-calendar/calendar.ics)
[![Subscribe Google Calendar](https://img.shields.io/badge/Subscribe-Google%20Calendar-blue?logo=google-calendar)](https://calendar.google.com/calendar/u/0/r?cid=https://Paxton-W.github.io/Wembley-stadium-event-calendar/calendar.ics)

This project scrapes **[Wembley Stadium – Events](https://www.wembleystadium.com/events)** daily and publishes an **auto-updating ICS calendar feed**.

Subscribers will automatically get new events or updates in their calendar app (iOS, macOS, Google Calendar, Android).

---

## 📅 Subscription URLs

### For iOS / macOS (Apple Calendar)

Use this link (opens subscription prompt automatically):

```
webcal://paxton-w.github.io/Wembley-stadium-event-calendar/calendar.ics
```

- On iPhone/iPad: Tap the link → **Add to Calendar**.
- On macOS Calendar app: Open the link with Calendar app.

### For Google Calendar / Android

1. Open Google Calendar in a **web browser** (desktop).
2. On the left, find **Other calendars** → click the **+** icon.
3. Choose **From URL**.
4. Paste: http://paxton-w.github.io/Wembley-stadium-event-calendar/calendar.ics
5. Click **Add calendar**. It will sync to your Google Calendar app.

---

## 🚀 How It Works

- **GitHub Pages** hosts the `calendar.ics` file at a public URL.
- **GitHub Actions (cron)** runs daily to:
  1. Scrape the Wembley Stadium events page.
  2. Parse event titles, dates, and times.
  3. Output them into an `.ics` file (UTF-8, UTC with `Europe/London` timezone metadata).
  4. Commit the updated file to the `/docs` folder.
- Subscribers' calendar apps periodically check the ICS URL and fetch updates.

---

## 🕒 Update Frequency

- **iOS/macOS**: refreshes periodically (Apple’s schedule, typically every few hours).
- **Google Calendar**: refreshes every few hours to 24h.
- Updates are incremental – existing events are updated, not duplicated (UIDs are stable).

---

## ⚙️ Development & Testing

1. Install dependencies:
   ```bash
   pip install beautifulsoup4 lxml
   ```
2. Run scraper locally:
   python scripts/generate_calendar.py

   This updates docs/calendar.ics.

---

📄 License

This project is for educational and personal use.
Wembley Stadium content and data belong to their respective owners.
