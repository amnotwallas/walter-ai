# Runbook: Audit Database Unavailable

## Overview
This runbook provides emergency resolution procedures for incidents where the SQLite audit database (`audit.db`) becomes locked, corrupted, or unavailable due to file locks or disk/permission issues.

## 1. Symptoms
* Unhandled database exceptions during audit logging or agent activity tracking.
* SQLite database file locks (`database is locked`) or read/write permission errors (`permission denied`).
* Elevating HTTP 500 error responses across API endpoints depending on database writes.

## 2. Active Alerts
* **`High5xxErrorRate`**
  * **Condition:** `HTTP 5xx rate / Total HTTP rate > 5%` over a 5-minute window.
  * **Severity:** `critical`

## 3. Incident Verification
Inspect structured JSON application logs for SQLite operational errors:
```json
{
  "level": "ERROR",
  "message": "Audit database operation failed",
  "error_type": "OperationalError",
  "exception": "sqlite3.OperationalError: database is locked"
}
```
Check application log output for `sqlite3.OperationalError` stack trace occurrences:
```bash
grep -i "sqlite3.OperationalError" /var/log/app/output.log
```

## 4. Immediate Mitigation Steps
1. **Verify Disk Usage & Permissions:**
   * Check available disk space: `df -h`
   * Check inode exhaustion: `df -i`
   * Verify read/write permissions on the database file directory: `ls -la data/audit.db`
2. **Handle Lock Files (`.db-journal` / `.db-wal` / `.db-shm`):**
   * Check if an ungracefully terminated process holds an open file lock: `lsof data/audit.db`
   * Stop the application service.
   * If database lock persists after service termination, verify journal status and safely clean stale lock files:
     ```bash
     rm -f data/audit.db-journal data/audit.db-wal data/audit.db-shm
     ```
3. **Repair SQLite Database (if corrupted):**
   * Attempt integrity check and recovery using standard `sqlite3` CLI:
     ```bash
     sqlite3 data/audit.db "PRAGMA integrity_check;"
     ```
   * If corruption is detected, perform recovery export/import:
     ```bash
     sqlite3 data/audit.db ".recover" | sqlite3 data/audit_recovered.db
     mv data/audit.db data/audit_corrupted.db.bak
     mv data/audit_recovered.db data/audit.db
     ```
4. **Restart Application Service:**
   * Restart API server and verify database connection health.

## 5. Prevention & Long-Term Solutions
* **Enable WAL Mode:** Configure SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) to support concurrent readers and writers without blocking.
* **Disk Space Alerting & Monitoring:** Configure node exporter / system health monitoring alerts when disk space drops below 15%.
* **Audit Database Migration:** Transition high-concurrency production deployments from SQLite to PostgreSQL or a managed DB backend.
