# Editorial Workflow Project (2026) Migration

We just need to update the mappings for Applications to accept new search fields.  Other mappings will be 
picked up automatically when the new version of the app starts.

```bash
python portality/migrate/ewp2026/update_mappings.py
```