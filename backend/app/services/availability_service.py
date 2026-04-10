import uuid
import datetime
from sqlalchemy.future import select
from app.models.domain import Appointment
from typing import List, Dict

class AvailabilityService:
    @staticmethod
    async def get_top_free_slots(db, business_id: str, business_type: str, next_days: int = 14) -> str:
        """
        Dynamically computes Top Free Slots.
        For clinics: Finds top 20 free 30-min slots during business hours.
        For hotels: Returns booked date ranges (nights) to allow the LLM to book anything outside them.
        """
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        # Apply +03:00 Timezone (AST/TRT) which is the target market zone
        now = (now_utc + datetime.timedelta(hours=3)).replace(tzinfo=None)
        future = now + datetime.timedelta(days=next_days)
        
        appointments_res = await db.execute(
            select(Appointment).where(
                Appointment.business_id == uuid.UUID(business_id), 
                Appointment.status.in_(["pending", "confirmed"]),
                Appointment.start_time >= now,
                Appointment.start_time <= future
            )
        )
        appts = appointments_res.scalars().all()

        if business_type.lower() == "hotel":
            # For Hotels, just return the exact blocked periods per room (staff_name handles room numbers usually)
            blocked = []
            for a in appts:
                blocked.append(f"Room/Entity '{a.staff_name or 'General'}': BLOCKED from {a.start_time.strftime('%Y-%m-%d')} to {a.end_time.strftime('%Y-%m-%d')}")
            if not blocked:
                return "All nights are currently FREE for the next 14 days."
            return "\n".join(blocked)
        else:
            # For Clinics / Retail Services
            # Assuming Business Hours 09:00 to 18:00
            # Let's compute up to 20 free 60-minute slots over the next few days
            free_slots = []
            current_day = now
            
            # Map booked intervals per staff
            booked_intervals = []
            for a in appts:
                booked_intervals.append({
                    "staff": a.staff_name or "General",
                    "start": a.start_time,
                    "end": a.end_time
                })

            for day_offset in range(next_days):
                target_date = now + datetime.timedelta(days=day_offset)
                if target_date.weekday() >= 6: continue # Skip Sunday generically if no specific DB field
                
                # Check hours 09:00 to 17:00
                for hour in range(9, 18):
                    slot_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    if slot_time < now:
                        continue
                        
                    # Is this slot booked?
                    slot_end = slot_time + datetime.timedelta(minutes=60)
                    is_booked = any(
                        b["start"] < slot_end and b["end"] > slot_time
                        for b in booked_intervals
                    )
                    
                    if not is_booked:
                        free_slots.append(slot_time.strftime("%Y-%m-%d %H:00"))
                        if len(free_slots) >= 20:
                            break
                if len(free_slots) >= 20:
                    break
            
            if not free_slots:
                return "No free slots available soon."
            
            return ", ".join(free_slots)
