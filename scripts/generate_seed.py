#!/usr/bin/env python3
"""
Seed Data Generator & Verifier for Foresight.
Generates and verifies 20 incidents and 40 deploys following SPEC Section 8 guidelines.
"""

import json
import sys
from pathlib import Path

SEED_INCIDENTS = [
  {
    "id": "INC-2024-001",
    "title": "Gateway timeout reduction caused downstream retry storm and double debits",
    "date": "2024-08-12T14:22:00Z",
    "service": "payments-gateway",
    "severity": "SEV-1",
    "root_cause_class": "retry_storm",
    "alert_text": "CRITICAL: payments-gateway 504 Gateway Timeout spike > 12% | Double-debit anomaly detected on UPI core",
    "error_logs": "2024-08-12 14:22:05 ERROR [gateway] Request timeout after 8000ms to partner bank NPCI\n2024-08-12 14:22:05 WARN [retry-handler] Retrying txn_981244 attempt 2/3\n2024-08-12 14:22:13 ERROR [upi-core] Duplicate debit request for txn_981244 (idempotency key missing in retry envelope)",
    "slack_excerpt": "Arjun: Why are we seeing double debits on UPI?\nPriya: The gateway retry timeout was lowered from 30s to 8s. NPCI processing takes ~12s under peak load, so gateway timed out prematurely and retried while first txn was pending!",
    "fix_attempts": [
      {
        "description": "Increase max retry attempts from 3 to 5",
        "outcome": "failed",
        "notes": "Made retry storm worse by cascading load back to NPCI."
      },
      {
        "description": "Rollback gateway retry timeout back to 30s and deploy emergency idempotency header patch",
        "outcome": "worked",
        "notes": "Resolved in 38 minutes. Restored normal debit processing."
      }
    ],
    "resolution_time_minutes": 38,
    "recurrence_link_id": "INC-2024-002"
  },
  {
    "id": "INC-2024-002",
    "title": "Aggressive retry config drift triggered duplicate debit cascade on card processor",
    "date": "2024-09-03T18:10:00Z",
    "service": "payments-gateway",
    "severity": "SEV-1",
    "root_cause_class": "retry_storm",
    "alert_text": "CRITICAL: card-processor latency breach 15s | High duplicate charge rate on Visa/Mastercard rail",
    "error_logs": "2024-09-03 18:10:12 ERROR [gateway] Gateway retry interval overridden to 5s without idempotency lock\n2024-09-03 18:10:17 ERROR [card-rail] Charge txn_339102 processed twice within 600ms window",
    "slack_excerpt": "DevOps: Config drift brought back the shortened 8s timeout! The idempotency check was bypassed in the non-blocking async queue.",
    "fix_attempts": [
      {
        "description": "Restart gateway nodes to flush config cache",
        "outcome": "temporary",
        "held_for_days": 9,
        "notes": "Temporary relief until config drift re-applied on auto-scale nodes."
      },
      {
        "description": "Enforce mandatory idempotency-key check before retry dispatch and lock timeout to >=25s",
        "outcome": "worked",
        "notes": "Fully resolved root cause."
      }
    ],
    "resolution_time_minutes": 45,
    "recurrence_link_id": "INC-2024-001"
  },
  {
    "id": "INC-2024-003",
    "title": "DB connection pool exhaustion during merchant settlement batch",
    "date": "2024-03-15T02:30:00Z",
    "service": "settlement-service",
    "severity": "SEV-2",
    "root_cause_class": "connection_pool_exhaustion",
    "alert_text": "HIGH: settlement-service PostgreSQL pool exhausted (100/100 active connections)",
    "error_logs": "2024-03-15 02:30:01 ERROR [db-pool] TimeoutAcquiringConnectionException: Pool max size reached (100)",
    "slack_excerpt": "Rohan: Settlement batch query had no limit statement and held connections open during webhooks.",
    "fix_attempts": [
      {
        "description": "Increase DB pool size to 200",
        "outcome": "failed",
        "notes": "Exhausted PG max_connections and crashed database server."
      },
      {
        "description": "Wrap settlement queries in explicit chunked transactions and separate webhook async queue",
        "outcome": "worked",
        "notes": "Pool utilization dropped to 25%."
      }
    ],
    "resolution_time_minutes": 52
  },
  {
    "id": "INC-2024-004",
    "title": "Expired TLS certificate on partner auth service broke payment webhooks",
    "date": "2024-04-10T09:05:00Z",
    "service": "auth-service",
    "severity": "SEV-2",
    "root_cause_class": "expired_certificate",
    "alert_text": "HIGH: auth-service SSLError SSLCertVerificationError certificate has expired",
    "error_logs": "2024-04-10 09:05:12 ERROR [auth] httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED]",
    "slack_excerpt": "Security: Internal CA certificate expired for auth.paynest.internal.",
    "fix_attempts": [
      {
        "description": "Disable SSL verification in httpx client",
        "outcome": "failed",
        "notes": "Blocked by security policy build check."
      },
      {
        "description": "Rotate internal TLS cert and automate cert-manager renewal alert 30 days prior",
        "outcome": "worked",
        "notes": "Rotated cert and restored webhook delivery."
      }
    ],
    "resolution_time_minutes": 22
  },
  {
    "id": "INC-2024-005",
    "title": "Redis cache eviction cascade caused auth token validation failure spree",
    "date": "2024-05-18T11:40:00Z",
    "service": "auth-service",
    "severity": "SEV-1",
    "root_cause_class": "cache_eviction_cascade",
    "alert_text": "CRITICAL: Redis memory usage 98% | maxmemory-policy allkeys-lru evicted active session keys",
    "error_logs": "2024-05-18 11:40:01 ERROR [auth] Key miss for session_88921. DB fallback latency spiked to 4500ms",
    "slack_excerpt": "Neha: Token cache was storing large analytics payloads alongside session keys.",
    "fix_attempts": [
      {
        "description": "Flushall Redis cache",
        "outcome": "failed",
        "notes": "Triggered complete thundering herd on primary Postgres DB."
      },
      {
        "description": "Separate Redis cluster for analytics vs sessions, update eviction policy to volatile-lru",
        "outcome": "worked",
        "notes": "Isolated auth session memory."
      }
    ],
    "resolution_time_minutes": 65
  },
  {
    "id": "INC-2024-006",
    "title": "Uncapped rate limiter memory leak on gateway ingress",
    "date": "2024-06-01T16:15:00Z",
    "service": "payments-gateway",
    "severity": "SEV-2",
    "root_cause_class": "rate_limit_misconfig",
    "alert_text": "HIGH: gateway OOMKilled pod restart count > 5 in 10m",
    "error_logs": "2024-06-01 16:15:22 CRITICAL [kernel] Out of memory: Kill process 1421 (python) score 950",
    "slack_excerpt": "Suresh: The new sliding window rate limiter saved client IP objects indefinitely in memory without TTL.",
    "fix_attempts": [
      {
        "description": "Increase pod memory limit from 2Gi to 4Gi",
        "outcome": "temporary",
        "held_for_days": 3,
        "notes": "Only delayed the OOM crash by 72 hours."
      },
      {
        "description": "Implement Redis-backed sliding window rate limiter with 60s TTL",
        "outcome": "worked",
        "notes": "Memory consumption stabilized at 350MB."
      }
    ],
    "resolution_time_minutes": 40
  },
  {
    "id": "INC-2024-007",
    "title": "Database failover packet loss triggered split-brain ledger entries",
    "date": "2024-07-04T22:00:00Z",
    "service": "ledger-service",
    "severity": "SEV-1",
    "root_cause_class": "db_failover_issue",
    "alert_text": "CRITICAL: Ledger sequence gap detected between Primary and Standby PG nodes",
    "error_logs": "2024-07-04 22:00:10 ERROR [ledger] Unique constraint violation on journal_entry_id 991823",
    "slack_excerpt": "DBA: Automatic failover promoted standby before sync replication completed during network drop.",
    "fix_attempts": [
      {
        "description": "Manual override replication lag flag",
        "outcome": "failed",
        "notes": "Created duplicate ledger balances that required manual reconciliation."
      },
      {
        "description": "Switch to synchronous_commit = remote_apply and add raft consensus lock on ledger writer",
        "outcome": "worked",
        "notes": "Guaranteed 0 data loss on failover."
      }
    ],
    "resolution_time_minutes": 110
  },
  {
    "id": "INC-2024-008",
    "title": "Kafka consumer group deadlock on corrupted payment payload",
    "date": "2024-08-28T08:30:00Z",
    "service": "notification-service",
    "severity": "SEV-2",
    "root_cause_class": "unhandled_poison_pill",
    "alert_text": "HIGH: Kafka consumer lag > 50,000 messages on topic payment-notifications",
    "error_logs": "2024-08-28 08:30:05 ERROR [consumer] JSONDecodeError: Expecting property name enclosed in double quotes",
    "slack_excerpt": "Karan: Consumer retried the malformed record indefinitely without offset commit.",
    "fix_attempts": [
      {
        "description": "Restart consumer pods",
        "outcome": "failed",
        "notes": "Immediately re-fetched the same poison pill record."
      },
      {
        "description": "Add Dead Letter Queue (DLQ) pattern with fallback schema validator and max 3 retries",
        "outcome": "worked",
        "notes": "Poison pill routed to DLQ, lag cleared in 5 minutes."
      }
    ],
    "resolution_time_minutes": 25
  },
  {
    "id": "INC-2024-009",
    "title": "HTTP client connection leak in payout status polling worker",
    "date": "2024-09-14T13:45:00Z",
    "service": "payout-service",
    "severity": "SEV-2",
    "root_cause_class": "connection_leak",
    "alert_text": "HIGH: Too many open files (socket descriptor limit reached: 1024)",
    "error_logs": "2024-09-14 13:45:02 ERROR [payout-worker] OSError: [Errno 24] Too many open files",
    "slack_excerpt": "Arjun: httpx.Client() was instantiated inside the loop instead of using a shared async context manager.",
    "fix_attempts": [
      {
        "description": "Increase ulimit -n to 65535",
        "outcome": "temporary",
        "held_for_days": 5,
        "notes": "Postponed crash until socket pool filled up again."
      },
      {
        "description": "Refactor httpx client to singleton lifecycle app state with pool limits",
        "outcome": "worked",
        "notes": "Open file descriptors stayed under 40 permanently."
      }
    ],
    "resolution_time_minutes": 35
  },
  {
    "id": "INC-2024-010",
    "title": "UPI SDK version mismatch broke QR payment payload decoding",
    "date": "2024-10-02T17:10:00Z",
    "service": "upi-core",
    "severity": "SEV-1",
    "root_cause_class": "bad_config_push",
    "alert_text": "CRITICAL: UPI QR parsing error rate > 40%",
    "error_logs": "2024-10-02 17:10:01 ERROR [upi-core] AttributeError: 'QRDecoder' object has no attribute 'parse_v2_payload'",
    "slack_excerpt": "Priya: Upgraded lib-upi dependency in config without updating core parser service binary.",
    "fix_attempts": [
      {
        "description": "Patch QR code handler with dynamic duck typing",
        "outcome": "failed",
        "notes": "Caused silent validation skips on v1 QR codes."
      },
      {
        "description": "Rollback deployment to build #482 and enforce strict lockfile version matching",
        "outcome": "worked",
        "notes": "Restored 100% QR parsing capability."
      }
    ],
    "resolution_time_minutes": 30
  },
  {
    "id": "INC-2024-011",
    "title": "Third-party webhook signature verification CPU bottleneck",
    "date": "2024-10-18T10:00:00Z",
    "service": "payments-gateway",
    "severity": "SEV-2",
    "root_cause_class": "cpu_exhaustion",
    "alert_text": "HIGH: Gateway CPU utilization 99% across all availability zones",
    "error_logs": "2024-10-18 10:00:05 WARN [gateway] High event loop lag: 840ms in HMAC SHA256 computation",
    "slack_excerpt": "Rohan: HMAC signature checking was running synchronously on the main asyncio thread.",
    "fix_attempts": [
      {
        "description": "Scale HPA from 10 to 30 pods",
        "outcome": "temporary",
        "held_for_days": 2,
        "notes": "Very expensive and did not solve event loop latency spikes."
      },
      {
        "description": "Offload HMAC payload verification to worker process pool (asyncio.to_thread)",
        "outcome": "worked",
        "notes": "CPU utilization stabilized at 30%."
      }
    ],
    "resolution_time_minutes": 48
  },
  {
    "id": "INC-2024-012",
    "title": "Config map update dropped fallback currency exchange rate matrix",
    "date": "2024-11-05T15:20:00Z",
    "service": "forex-service",
    "severity": "SEV-1",
    "root_cause_class": "bad_config_push",
    "alert_text": "CRITICAL: Cross-border payments failing with 500 Invalid Currency Pair",
    "error_logs": "2024-11-05 15:20:00 ERROR [forex] KeyError: 'USD_INR' in active rate map",
    "slack_excerpt": "DevOps: Helm deployment stripped default fallback keys from configmap YAML.",
    "fix_attempts": [
      {
        "description": "Inject missing key via kubectl edit configmap live",
        "outcome": "temporary",
        "held_for_days": 1,
        "notes": "Overwritten on next CI/CD pipeline run."
      },
      {
        "description": "Add Pydantic schema validation for ConfigMap on service startup with fail-fast check",
        "outcome": "worked",
        "notes": "Prevents invalid config deployment permanently."
      }
    ],
    "resolution_time_minutes": 28
  },
  {
    "id": "INC-2024-013",
    "title": "Unindexed transaction query caused PostgreSQL disk I/O saturation",
    "date": "2024-11-20T20:15:00Z",
    "service": "merchant-dashboard",
    "severity": "SEV-2",
    "root_cause_class": "missing_database_index",
    "alert_text": "HIGH: Postgres Aurora Read IOPS saturated | Query duration > 15000ms",
    "error_logs": "2024-11-20 20:15:00 WARN [pg_stat_activity] Sequential scan on transactions table (45M rows)",
    "slack_excerpt": "Suresh: New merchant filtering endpoint searched created_at without compound index on merchant_id.",
    "fix_attempts": [
      {
        "description": "Increase Aurora instance size to db.r6g.4xlarge",
        "outcome": "failed",
        "notes": "Disk IOPS still maxed out during peak query surges."
      },
      {
        "description": "Create CONCURRENTLY index on transactions(merchant_id, created_at DESC)",
        "outcome": "worked",
        "notes": "Query time reduced from 15s to 4ms."
      }
    ],
    "resolution_time_minutes": 55
  },
  {
    "id": "INC-2024-014",
    "title": "Circuit breaker threshold misconfiguration prematurely disabled card processing",
    "date": "2024-12-01T08:00:00Z",
    "service": "payments-gateway",
    "severity": "SEV-1",
    "root_cause_class": "rate_limit_misconfig",
    "alert_text": "CRITICAL: Card payment circuit breaker OPEN state triggered for 100% traffic",
    "error_logs": "2024-12-01 08:00:01 ERROR [circuit-breaker] Failure threshold 5% reached (consecutive 3 errors in 10s window)",
    "slack_excerpt": "Arjun: Circuit breaker failure threshold was set to 5% instead of 50% during maintenance test.",
    "fix_attempts": [
      {
        "description": "Force circuit breaker state to CLOSED via admin CLI",
        "outcome": "temporary",
        "held_for_days": 1,
        "notes": "Tripped open again after next single network glitch."
      },
      {
        "description": "Fix threshold to 50% and sliding window to 100 requests minimum sample size",
        "outcome": "worked",
        "notes": "Circuit breaker behavior normal."
      }
    ],
    "resolution_time_minutes": 18
  },
  {
    "id": "INC-2024-015",
    "title": "Log parsing buffer overflow crashed payment audit tailer",
    "date": "2024-12-12T12:30:00Z",
    "service": "audit-service",
    "severity": "SEV-3",
    "root_cause_class": "buffer_overflow",
    "alert_text": "MEDIUM: audit-service pod crashing with SIGSEGV in log parsing thread",
    "error_logs": "2024-12-12 12:30:04 FATAL [audit] BufferOverflowError: Log line exceeded 65536 bytes",
    "slack_excerpt": "Neha: A vendor sent an ultra-large base64 blob in the log context string.",
    "fix_attempts": [
      {
        "description": "Truncate log lines in FluentBit daemon",
        "outcome": "worked",
        "notes": "Sanitized log pipeline and prevented parser crash."
      }
    ],
    "resolution_time_minutes": 15
  },
  {
    "id": "INC-2025-001",
    "title": "Third-party gateway retry interval mismatch created payment duplication loop",
    "date": "2025-01-08T16:40:00Z",
    "service": "payments-gateway",
    "severity": "SEV-1",
    "root_cause_class": "retry_storm",
    "alert_text": "CRITICAL: Duplicate charge alerts from Razorpay connector | Retry interval conflict",
    "error_logs": "2025-01-08 16:40:10 ERROR [gateway] Retrying payment txn_77123 after 6s timeout; Razorpay SLA is 15s",
    "slack_excerpt": "Priya: Another retry timeout change! Gateway timeout of 6s was shorter than upstream provider processing SLA.",
    "fix_attempts": [
      {
        "description": "Set retry backoff to fixed 10s",
        "outcome": "failed",
        "notes": "Still shorter than Razorpay tail latency."
      },
      {
        "description": "Set gateway timeout to 30s minimum and mandate idempotency header on all retry attempts",
        "outcome": "worked",
        "notes": "Zero duplicate debits since fix."
      }
    ],
    "resolution_time_minutes": 42,
    "recurrence_link_id": "INC-2024-001"
  },
  {
    "id": "INC-2025-002",
    "title": "Asynchronous event queue backpressure dropped refund confirmation webhooks",
    "date": "2025-01-22T19:15:00Z",
    "service": "refund-service",
    "severity": "SEV-2",
    "root_cause_class": "queue_backpressure",
    "alert_text": "HIGH: Refund webhook delivery failure rate 25% | RabbitMQ queue memory alarm",
    "error_logs": "2025-01-22 19:15:02 WARN [refunds] Queue full: drop_head policy dropped message ref_99214",
    "slack_excerpt": "Karan: Queue overflow policy was set to drop silently instead of blocking/nack.",
    "fix_attempts": [
      {
        "description": "Increase queue depth limit from 10,000 to 100,000",
        "outcome": "failed",
        "notes": "Ran out of RabbitMQ RAM and crashed broker."
      },
      {
        "description": "Change queue policy to rejection with dead-letter routing and add worker auto-scaler",
        "outcome": "worked",
        "notes": "Cleared backpressure safely."
      }
    ],
    "resolution_time_minutes": 33
  },
  {
    "id": "INC-2025-003",
    "title": "Distributed lock TTL expiry caused double settlement run",
    "date": "2025-02-05T03:10:00Z",
    "service": "settlement-service",
    "severity": "SEV-1",
    "root_cause_class": "lock_expiry_race",
    "alert_text": "CRITICAL: Duplicate batch settlement generated for Merchant #4021",
    "error_logs": "2025-02-05 03:10:00 ERROR [settlement] Lock 'settlement_batch_4021' expired after 30s while process was active",
    "slack_excerpt": "Rohan: Long DB transaction exceeded Redis lock TTL, so secondary worker acquired lock and ran settlement again.",
    "fix_attempts": [
      {
        "description": "Increase Redis lock TTL from 30s to 300s",
        "outcome": "temporary",
        "held_for_days": 14,
        "notes": "Worked until a large merchant batch took 310s."
      },
      {
        "description": "Implement Redlock with automatic TTL renewal watchdog thread (lock heartbeat)",
        "outcome": "worked",
        "notes": "Prevented lock expiry race indefinitely."
      }
    ],
    "resolution_time_minutes": 50
  },
  {
    "id": "INC-2025-004",
    "title": "Strict schema validation rejection on partner API response extension",
    "date": "2025-02-14T11:00:00Z",
    "service": "payments-gateway",
    "severity": "SEV-2",
    "root_cause_class": "schema_validation_failure",
    "alert_text": "HIGH: Bank connector response deserialization error count > 500/min",
    "error_logs": "2025-02-14 11:00:01 ERROR [pydantic] ValidationError: Extra fields not permitted: 'bank_reference_subcode'",
    "slack_excerpt": "Suresh: Upstream bank added a new non-breaking field to their JSON response, but our Pydantic model had extra='forbid'.",
    "fix_attempts": [
      {
        "description": "Deploy emergency hotfix setting extra='ignore' in response models",
        "outcome": "worked",
        "notes": "Restored API compatibility instantly."
      }
    ],
    "resolution_time_minutes": 14
  },
  {
    "id": "INC-2025-005",
    "title": "Graceful degradation failure on fraud scoring service offline",
    "date": "2025-02-28T14:50:00Z",
    "service": "fraud-service",
    "severity": "SEV-1",
    "root_cause_class": "missing_fallback_degradation",
    "alert_text": "CRITICAL: Payment flow blocked for 100% users due to fraud-service 503 response",
    "error_logs": "2025-02-28 14:50:05 ERROR [checkout] FraudCheckException: Fraud service unreachable. Payment aborted.",
    "slack_excerpt": "Arjun: Payment checkout had a hard dependency on fraud score without fallback path when fraud service timed out.",
    "fix_attempts": [
      {
        "description": "Bypass fraud service completely in code",
        "outcome": "failed",
        "notes": "Exposed platform to unvetted high-risk transactions."
      },
      {
        "description": "Implement rule-based local fallback mode and circuit breaker for fraud scoring API",
        "outcome": "worked",
        "notes": "Allows low-risk payments with delayed async fraud scoring during outage."
      }
    ],
    "resolution_time_minutes": 31
  }
]

SEED_DEPLOYS = [
  {
    "id": "DEP-2024-001",
    "title": "Lower gateway retry timeout from 30s to 8s",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Arjun",
    "date": "2024-08-12T14:00:00Z",
    "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000"],
    "outcome": "incident",
    "incident_id": "INC-2024-001"
  },
  {
    "id": "DEP-2024-002",
    "title": "Rollback gateway retry timeout to 30s and deploy idempotency header",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Priya",
    "date": "2024-08-12T14:58:00Z",
    "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=30000", "ENFORCE_IDEMPOTENCY_HEADER=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-003",
    "title": "Sync retry config across gateway staging cluster",
    "service": "payments-gateway",
    "environment": "staging",
    "author": "Arjun",
    "date": "2024-08-20T10:15:00Z",
    "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=30000"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-004",
    "title": "Card processor config sync update",
    "service": "payments-gateway",
    "environment": "production",
    "author": "DevOps",
    "date": "2024-09-03T18:00:00Z",
    "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000", "CARD_RETRY_INTERVAL_MS=5000"],
    "outcome": "incident",
    "incident_id": "INC-2024-002"
  },
  {
    "id": "DEP-2024-005",
    "title": "Enforce mandatory idempotency check and lock timeout >=25s",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Priya",
    "date": "2024-09-03T18:50:00Z",
    "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=25000", "STRICT_IDEMPOTENCY_LOCK=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-006",
    "title": "Settlement service query optimization release",
    "service": "settlement-service",
    "environment": "production",
    "author": "Rohan",
    "date": "2024-03-15T02:00:00Z",
    "config_changes": ["DB_POOL_SIZE=100"],
    "outcome": "incident",
    "incident_id": "INC-2024-003"
  },
  {
    "id": "DEP-2024-007",
    "title": "Chunked settlement transaction migration",
    "service": "settlement-service",
    "environment": "production",
    "author": "Rohan",
    "date": "2024-03-15T03:20:00Z",
    "config_changes": ["DB_POOL_SIZE=50", "CHUNKED_TRANSACTIONS=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-008",
    "title": "Rotate internal auth certificates",
    "service": "auth-service",
    "environment": "production",
    "author": "SecurityBot",
    "date": "2024-04-10T09:25:00Z",
    "config_changes": ["TLS_CERT_PATH=/etc/certs/2024-v2.crt"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-009",
    "title": "Separate Redis clusters for session and analytics",
    "service": "auth-service",
    "environment": "production",
    "author": "Neha",
    "date": "2024-05-18T12:45:00Z",
    "config_changes": ["REDIS_EVICTION_POLICY=volatile-lru"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-010",
    "title": "Sliding window rate limiter patch",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Suresh",
    "date": "2024-06-01T17:00:00Z",
    "config_changes": ["RATE_LIMITER_BACKEND=redis", "RATE_LIMITER_TTL=60"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-011",
    "title": "Synchronous commit and raft lock for ledger writer",
    "service": "ledger-service",
    "environment": "production",
    "author": "DBA",
    "date": "2024-07-04T23:50:00Z",
    "config_changes": ["SYNCHRONOUS_COMMIT=remote_apply"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-012",
    "title": "Add Dead Letter Queue to notification Kafka consumer",
    "service": "notification-service",
    "environment": "production",
    "author": "Karan",
    "date": "2024-08-28T08:55:00Z",
    "config_changes": ["ENABLE_DLQ=true", "MAX_CONSUMER_RETRIES=3"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-013",
    "title": "Refactor httpx client to app singleton lifecycle",
    "service": "payout-service",
    "environment": "production",
    "author": "Arjun",
    "date": "2024-09-14T14:20:00Z",
    "config_changes": ["HTTP_POOL_MAX_SIZE=50"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-014",
    "title": "Rollback upi-core build to #482",
    "service": "upi-core",
    "environment": "production",
    "author": "Priya",
    "date": "2024-10-02T17:40:00Z",
    "config_changes": ["UPI_CORE_BUILD_ID=482"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-015",
    "title": "Offload HMAC signature check to threadpool worker",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Rohan",
    "date": "2024-10-18T10:48:00Z",
    "config_changes": ["WORKER_THREAD_POOL_SIZE=16"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-016",
    "title": "Pydantic ConfigMap schema validation on startup",
    "service": "forex-service",
    "environment": "production",
    "author": "DevOps",
    "date": "2024-11-05T15:48:00Z",
    "config_changes": ["VALIDATE_CONFIG_SCHEMA_STRICT=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-017",
    "title": "Add concurrent index on transactions table",
    "service": "merchant-dashboard",
    "environment": "production",
    "author": "Suresh",
    "date": "2024-11-20T21:10:00Z",
    "config_changes": [],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-018",
    "title": "Adjust circuit breaker failure threshold and sample window",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Arjun",
    "date": "2024-12-01T08:18:00Z",
    "config_changes": ["CIRCUIT_BREAKER_FAILURE_THRESHOLD=50", "CIRCUIT_BREAKER_MIN_SAMPLES=100"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2024-019",
    "title": "Truncate log lines in FluentBit daemon",
    "service": "audit-service",
    "environment": "production",
    "author": "Neha",
    "date": "2024-12-12T12:45:00Z",
    "config_changes": ["MAX_LOG_LINE_BYTES=65536"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-020",
    "title": "Lower Razorpay connector retry timeout from 15s to 6s",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Priya",
    "date": "2025-01-08T16:00:00Z",
    "config_changes": ["RAZORPAY_RETRY_TIMEOUT_MS=6000"],
    "outcome": "incident",
    "incident_id": "INC-2025-001"
  },
  {
    "id": "DEP-2025-021",
    "title": "Set gateway retry timeout to 30s and mandate idempotency",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Priya",
    "date": "2025-01-08T17:22:00Z",
    "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=30000", "ENFORCE_IDEMPOTENCY_HEADER=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-022",
    "title": "RabbitMQ dead-letter routing and auto-scaler policy",
    "service": "refund-service",
    "environment": "production",
    "author": "Karan",
    "date": "2025-01-22T19:48:00Z",
    "config_changes": ["QUEUE_OVERFLOW_REJECT_DLQ=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-023",
    "title": "Redlock with watchdog thread for settlement worker",
    "service": "settlement-service",
    "environment": "production",
    "author": "Rohan",
    "date": "2025-02-05T04:00:00Z",
    "config_changes": ["REDLOCK_WATCHDOG_ENABLE=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-024",
    "title": "Pydantic extra fields setting to ignore in responses",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Suresh",
    "date": "2025-02-14T11:14:00Z",
    "config_changes": ["RESPONSE_MODEL_EXTRA=ignore"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-025",
    "title": "Local fallback mode and circuit breaker for fraud scoring API",
    "service": "fraud-service",
    "environment": "production",
    "author": "Arjun",
    "date": "2025-02-28T15:21:00Z",
    "config_changes": ["FRAUD_SERVICE_FALLBACK_ENABLE=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-026",
    "title": "Routine DB maintenance and re-index",
    "service": "ledger-service",
    "environment": "production",
    "author": "DBA",
    "date": "2025-03-01T01:00:00Z",
    "config_changes": [],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-027",
    "title": "Update merchant webhook retry backoff policy",
    "service": "notification-service",
    "environment": "production",
    "author": "Karan",
    "date": "2025-03-02T10:00:00Z",
    "config_changes": ["WEBHOOK_MAX_RETRIES=5"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-028",
    "title": "Upgrade FastAPI and Pydantic v2 dependencies",
    "service": "auth-service",
    "environment": "staging",
    "author": "Neha",
    "date": "2025-03-03T14:00:00Z",
    "config_changes": [],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-029",
    "title": "Enable HTTP2 keep-alive connections on gateway",
    "service": "payments-gateway",
    "environment": "staging",
    "author": "Arjun",
    "date": "2025-03-04T09:30:00Z",
    "config_changes": ["HTTP2_ENABLE=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-030",
    "title": "Bump UPI SDK version to 2.4.1",
    "service": "upi-core",
    "environment": "staging",
    "author": "Priya",
    "date": "2025-03-04T16:00:00Z",
    "config_changes": ["UPI_SDK_VERSION=2.4.1"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-031",
    "title": "Add Prometheus metrics exporter to payout service",
    "service": "payout-service",
    "environment": "production",
    "author": "Arjun",
    "date": "2025-03-05T08:20:00Z",
    "config_changes": ["METRICS_PORT=9090"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-032",
    "title": "Tune Aurora connection pool min/max boundaries",
    "service": "merchant-dashboard",
    "environment": "production",
    "author": "Suresh",
    "date": "2025-03-05T11:00:00Z",
    "config_changes": ["DB_MIN_CONNECTIONS=10", "DB_MAX_CONNECTIONS=40"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-033",
    "title": "Enable JSON log formatting for audit service",
    "service": "audit-service",
    "environment": "production",
    "author": "Neha",
    "date": "2025-03-06T13:10:00Z",
    "config_changes": ["LOG_FORMAT=json"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-034",
    "title": "Add caching layer for exchange rate requests",
    "service": "forex-service",
    "environment": "production",
    "author": "DevOps",
    "date": "2025-03-06T15:45:00Z",
    "config_changes": ["CACHE_TTL_SECONDS=300"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-035",
    "title": "Rotate JWT signing keys",
    "service": "auth-service",
    "environment": "production",
    "author": "SecurityBot",
    "date": "2025-03-07T02:00:00Z",
    "config_changes": ["JWT_KEY_VERSION=v4"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-036",
    "title": "Update settlement reconciliation batch cron schedule",
    "service": "settlement-service",
    "environment": "production",
    "author": "Rohan",
    "date": "2025-03-07T05:00:00Z",
    "config_changes": ["CRON_SCHEDULE=0 2 * * *"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-037",
    "title": "Optimize Redis memory footprint in gateway rate-limiter",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Suresh",
    "date": "2025-03-07T09:15:00Z",
    "config_changes": [],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-038",
    "title": "Scale payout worker pod count from 4 to 8",
    "service": "payout-service",
    "environment": "production",
    "author": "Arjun",
    "date": "2025-03-07T11:30:00Z",
    "config_changes": ["WORKER_REPLICAS=8"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-039",
    "title": "Enable distributed tracing headers propagation",
    "service": "upi-core",
    "environment": "production",
    "author": "Priya",
    "date": "2025-03-07T14:00:00Z",
    "config_changes": ["TRACING_ENABLED=true"],
    "outcome": "clean"
  },
  {
    "id": "DEP-2025-040",
    "title": "Lower gateway retry timeout from 30s to 8s (Arjun Friday 5:40 PM PR)",
    "service": "payments-gateway",
    "environment": "production",
    "author": "Arjun",
    "date": "2025-03-07T17:40:00Z",
    "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000"],
    "outcome": "degraded",
    "notes": "Arjun PR under review by Foresight deploy-safety agent."
  }
]


def generate_seed_files(seed_dir: Path):
    seed_dir.mkdir(parents=True, exist_ok=True)

    incidents_path = seed_dir / "incidents.json"
    deploys_path = seed_dir / "deploys.json"

    with open(incidents_path, "w", encoding="utf-8") as f:
        json.dump(SEED_INCIDENTS, f, indent=2)

    with open(deploys_path, "w", encoding="utf-8") as f:
        json.dump(SEED_DEPLOYS, f, indent=2)

    print(f"Generated {len(SEED_INCIDENTS)} incidents -> {incidents_path}")
    print(f"Generated {len(SEED_DEPLOYS)} deploys -> {deploys_path}")


def validate_seed_data(incidents: list[dict], deploys: list[dict]) -> bool:
    print(f"Checking incidents count: {len(incidents)} (expected 20)")
    assert len(incidents) == 20, f"Expected 20 incidents, got {len(incidents)}"

    print(f"Checking deploys count: {len(deploys)} (expected 40)")
    assert len(deploys) == 40, f"Expected 40 deploys, got {len(deploys)}"

    retry_pattern_incidents = [
        inc for inc in incidents
        if "retry" in inc["title"].lower() or "retry" in inc.get("root_cause_class", "").lower()
    ]
    print(f"Found {len(retry_pattern_incidents)} retry-pattern incidents")
    assert len(retry_pattern_incidents) >= 3, "Expected at least 3 retry pattern incidents"

    temp_fixes = []
    for inc in incidents:
        for fix in inc.get("fix_attempts", []):
            if fix.get("outcome") == "temporary":
                temp_fixes.append(fix)

    print(f"Found {len(temp_fixes)} temporary fix attempts")
    assert len(temp_fixes) >= 1, "Expected at least 1 temporary fix attempt"
    assert any("held_for_days" in fix for fix in temp_fixes), "Temporary fix missing 'held_for_days'"

    for inc in incidents:
        for field in ["id", "title", "date", "service", "severity", "root_cause_class", "alert_text", "error_logs", "slack_excerpt", "fix_attempts"]:
            assert field in inc, f"Incident {inc.get('id')} missing field {field}"

    for dep in deploys:
        for field in ["id", "title", "service", "environment", "author", "date", "config_changes", "outcome"]:
            assert field in dep, f"Deploy {dep.get('id')} missing field {field}"

    print("✅ All seed data validations passed successfully!")
    return True


def main():
    seed_dir = Path(__file__).parent.parent / "data" / "seed"
    incidents_path = seed_dir / "incidents.json"
    deploys_path = seed_dir / "deploys.json"

    # Always ensure files are generated / written
    generate_seed_files(seed_dir)

    with open(incidents_path, "r", encoding="utf-8") as f:
        incidents = json.load(f)

    with open(deploys_path, "r", encoding="utf-8") as f:
        deploys = json.load(f)

    validate_seed_data(incidents, deploys)


if __name__ == "__main__":
    main()
