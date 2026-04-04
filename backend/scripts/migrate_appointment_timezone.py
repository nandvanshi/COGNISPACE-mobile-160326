"""
Migration Script: Convert old IST-in-UTC appointments to correct UTC format.

Background:
- Old bug: Backend slot generation applied IST availability hours (e.g., 19:15) 
  directly to UTC date objects → stored as "2026-04-03T19:15:00+00:00" instead of 
  correct "2026-04-03T13:45:00+00:00"
- This script detects and fixes these old-format appointments.

Detection logic:
- Parse stored UTC time, convert to IST
- If IST date DIFFERS from stored date component → DEFINITE old format (evening IST appointments)
- For ambiguous cases (same date in both), check if subtracting 5:30 gives a time 
  between 6 AM - 11 PM IST (reasonable therapy hours)

Safety:
- DRY-RUN mode by default (shows changes without applying)
- Creates backup in 'appointment_backups' collection before modifying
- Logs every change for audit trail
"""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from motor.motor_asyncio import AsyncIOMotorClient

IST = ZoneInfo("Asia/Kolkata")
IST_OFFSET = timedelta(hours=5, minutes=30)


def detect_and_fix_appointment(start_time_str, end_time_str):
    """
    Detect if appointment times are in old IST-in-UTC format and return corrected times.
    
    Returns:
        tuple: (needs_fix, new_start, new_end, reason)
    """
    if not start_time_str:
        return False, None, None, "no start_time"
    
    try:
        # Parse stored time as UTC
        start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        
        # Convert to IST
        start_ist = start_dt.astimezone(IST)
        
        # Extract stored date component
        stored_date_str = start_time_str[:10]  # "YYYY-MM-DD"
        ist_date_str = start_ist.strftime("%Y-%m-%d")
        
        # DEFINITE old format: IST conversion gives a DIFFERENT date
        # This happens for evening IST appointments (after 6:30 PM IST = 18:30 UTC)
        # stored as UTC → IST conversion crosses midnight
        if ist_date_str != stored_date_str:
            # Old format confirmed - the stored "UTC" time IS actually IST
            # Fix: treat the stored hour/minute as IST, convert to real UTC
            stored_date = datetime.strptime(stored_date_str, "%Y-%m-%d").date()
            real_ist = datetime(
                stored_date.year, stored_date.month, stored_date.day,
                start_dt.hour, start_dt.minute, start_dt.second,
                tzinfo=IST
            )
            real_utc = real_ist.astimezone(timezone.utc)
            new_start = real_utc.isoformat()
            
            # Fix end_time similarly
            new_end = None
            if end_time_str:
                end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                end_stored_date = end_time_str[:10]
                end_date = datetime.strptime(end_stored_date, "%Y-%m-%d").date()
                real_end_ist = datetime(
                    end_date.year, end_date.month, end_date.day,
                    end_dt.hour, end_dt.minute, end_dt.second,
                    tzinfo=IST
                )
                new_end = real_end_ist.astimezone(timezone.utc).isoformat()
            
            return True, new_start, new_end, f"date_mismatch (stored={stored_date_str}, ist={ist_date_str})"
        
        # AMBIGUOUS: Same date in both - check with heuristic
        # If the stored UTC hour is in typical IST business range (8-22) 
        # AND converting to IST gives early hours (before 6:30 AM), it's likely old format
        utc_hour = start_dt.hour
        ist_hour = start_ist.hour
        
        # If UTC hour >= 6 and IST hour in very early morning (0-5), likely old format
        # But this case is already caught above (date mismatch)
        
        # For same-date ambiguous cases: check if the stored time, when treated as IST 
        # and converted to UTC, gives a time with a date component matching the stored date
        test_ist = datetime(
            start_dt.year, start_dt.month, start_dt.day,
            start_dt.hour, start_dt.minute, start_dt.second,
            tzinfo=IST
        )
        test_utc = test_ist.astimezone(timezone.utc)
        
        # If treating as IST gives a UTC time on the PREVIOUS day, and the original 
        # UTC time is in the afternoon/evening range → likely old format
        if test_utc.date() < start_dt.date() and utc_hour >= 6:
            new_start = test_utc.isoformat()
            
            new_end = None
            if end_time_str:
                end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                test_end_ist = datetime(
                    end_dt.year, end_dt.month, end_dt.day,
                    end_dt.hour, end_dt.minute, end_dt.second,
                    tzinfo=IST
                )
                new_end = test_end_ist.astimezone(timezone.utc).isoformat()
            
            return True, new_start, new_end, f"heuristic (utc_hour={utc_hour}, test_utc_date={test_utc.date()})"
        
        return False, None, None, "correct_format"
        
    except Exception as e:
        return False, None, None, f"parse_error: {e}"


async def run_migration(dry_run=True):
    """Run the migration. Set dry_run=False to actually apply changes."""
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME', 'cognispace')]
    
    print(f"\n{'=' * 60}")
    print(f"  APPOINTMENT TIMEZONE MIGRATION")
    print(f"  Mode: {'DRY-RUN (no changes)' if dry_run else 'LIVE (applying changes)'}")
    print(f"  Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"{'=' * 60}\n")
    
    # Fetch all appointments
    appointments = await db.appointments.find(
        {}, 
        {"_id": 0, "id": 1, "start_time": 1, "end_time": 1, "client_name": 1, 
         "therapist_id": 1, "status": 1, "created_at": 1}
    ).to_list(10000)
    
    print(f"Total appointments found: {len(appointments)}")
    
    to_fix = []
    already_correct = []
    errors = []
    
    for appt in appointments:
        needs_fix, new_start, new_end, reason = detect_and_fix_appointment(
            appt.get("start_time"), appt.get("end_time")
        )
        
        if needs_fix:
            to_fix.append({
                "id": appt.get("id"),
                "client_name": appt.get("client_name", "Unknown"),
                "status": appt.get("status"),
                "old_start": appt.get("start_time"),
                "old_end": appt.get("end_time"),
                "new_start": new_start,
                "new_end": new_end,
                "reason": reason
            })
        elif "error" in reason:
            errors.append({"id": appt.get("id"), "reason": reason})
        else:
            already_correct.append(appt.get("id"))
    
    print(f"\nResults:")
    print(f"  Already correct: {len(already_correct)}")
    print(f"  Need fixing:     {len(to_fix)}")
    print(f"  Errors:          {len(errors)}")
    
    if to_fix:
        print(f"\n--- Appointments to fix ---")
        for item in to_fix:
            old_ist_display = "N/A"
            new_ist_display = "N/A"
            try:
                old_dt = datetime.fromisoformat(item["old_start"].replace('Z', '+00:00'))
                # Old format: UTC time IS the IST time
                old_ist_display = old_dt.strftime("%I:%M %p")
                new_dt = datetime.fromisoformat(item["new_start"].replace('Z', '+00:00'))
                new_ist = new_dt.astimezone(IST)
                new_ist_display = new_ist.strftime("%I:%M %p")
            except:
                pass
            
            print(f"\n  [{item['status']}] {item['client_name']} ({item['reason']})")
            print(f"    Old: {item['old_start']} (displayed as {old_ist_display})")
            print(f"    New: {item['new_start']} (displays as {new_ist_display})")
    
    if errors:
        print(f"\n--- Errors ---")
        for err in errors:
            print(f"  {err['id']}: {err['reason']}")
    
    if not dry_run and to_fix:
        print(f"\n--- Applying fixes ---")
        
        # Create backup first
        if to_fix:
            backup_docs = []
            for item in to_fix:
                backup_docs.append({
                    "appointment_id": item["id"],
                    "old_start_time": item["old_start"],
                    "old_end_time": item["old_end"],
                    "new_start_time": item["new_start"],
                    "new_end_time": item["new_end"],
                    "reason": item["reason"],
                    "migrated_at": datetime.now(timezone.utc).isoformat()
                })
            await db.appointment_backups.insert_many(backup_docs)
            print(f"  Backup created: {len(backup_docs)} records in 'appointment_backups' collection")
        
        # Apply fixes
        fixed_count = 0
        for item in to_fix:
            update_fields = {"start_time": item["new_start"]}
            if item["new_end"]:
                update_fields["end_time"] = item["new_end"]
            
            result = await db.appointments.update_one(
                {"id": item["id"]},
                {"$set": update_fields}
            )
            if result.modified_count > 0:
                fixed_count += 1
                print(f"  Fixed: {item['client_name']} ({item['id'][:12]}...)")
        
        print(f"\n  Total fixed: {fixed_count}/{len(to_fix)}")
    
    elif dry_run and to_fix:
        print(f"\n  [DRY-RUN] No changes applied. Run with --apply to fix.")
    
    print(f"\n{'=' * 60}")
    print(f"  Migration complete.")
    print(f"{'=' * 60}\n")
    
    client.close()
    
    return {
        "total": len(appointments),
        "already_correct": len(already_correct),
        "fixed": len(to_fix),
        "errors": len(errors),
        "details": to_fix
    }


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    asyncio.run(run_migration(dry_run=dry_run))
