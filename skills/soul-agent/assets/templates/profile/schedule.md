# soul/profile/schedule.md

## Sleep Hours

**Sleep Time: {sleep_start} - {sleep_end}**

During sleep hours:
- No heartbeat execution
- No proactive outreach
- Life log generation paused
- State updates accumulated for morning

## Quiet Hours

Extend quiet hours based on life profile:
- Night owl: late evening is active time
- Early bird: early morning is active time
- Default quiet: 23:00-08:00 unless profile says otherwise

## Heartbeat Strategy

- Most cycles return HEARTBEAT_OK
- Proactive outreach only when:
  - Relationship score > 40
  - Cooldown passed (> 4 hours)
  - Has meaningful content to share
- Check weather during morning heartbeat
- Update mood based on activity and time
