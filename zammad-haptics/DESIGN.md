# Zammad → MX Master 4 Haptic Bridge (design)

Webhook-based bridge: Zammad triggers POST a small local HTTP relay on this machine,
which verifies an HMAC and forwards to HapticWeb. Chosen over API polling / DOM watching
because the user is always on the same LAN as the Zammad instance
(`helpdesk.agmamito.com`) — webhooks give real-time delivery with no polling cost.

## Architecture

```
Zammad trigger ──(POST, HMAC signed)──▶ relay (this PC :41500)
                                           │
                                           ▼
                          https://local.jmw.nz:41443/haptic/<wave>
                                    (HapticWeb plugin)
```

- **Relay**: `zammad-haptics/zammad_relay.py` — stdlib `http.server`, binds on
  `0.0.0.0:41500`, single-threaded, forwards synchronously to HapticWeb in a background
  thread (same pattern as `haptics_daemon_win.py`).
- **Auth**: HMAC-SHA256 on request body with a shared secret. Rejects unsigned or
  mismatched requests. Secret generated at install time and printed to console for
  pasting into Zammad's webhook config.
- **Startup**: scheduled task via `zammad-haptics/install.ps1`, same pattern as the
  OS haptics daemon. Installer also adds a Windows Firewall rule allowing inbound
  TCP 41500 on the `Private` profile only.

## Event → waveform mapping

Waveforms chosen **strictly from the set not already used** by the browser extension,
OS daemons, or Claude Code hooks — so every Zammad haptic is instantly distinguishable
from every other haptic in the stack.

| Zammad event | Waveform | Why this one |
|---|---|---|
| Ticket created | `ringing` | Doorbell metaphor — "someone's calling for help" |
| Customer reply on existing ticket | `happy_alert` | Short, positive "heads-up" |
| Escalation / SLA breach | `mad` | Aggressive pattern, matches urgency |

### Waveform inventory (all 15)

- **Used elsewhere in the project:** `damp_collision`, `subtle_collision`,
  `sharp_collision`, `damp_state_change`, `completed`, `angry_alert`,
  `knock`, `jingle` (8)
- **Reserved for Zammad above:** `ringing`, `happy_alert`, `mad` (3)
- **Still free for future events:** `sharp_state_change`, `firework`, `wave`,
  `square` (4)

## Zammad side — to configure in admin UI

1. **Admin → Webhook → New**
   - URL: `http://<this-pc-lan-ip>:41500/zammad`
   - HMAC signing: enabled, secret = value printed by `install.ps1`
   - (Optional) Basic auth / additional headers: none
2. **Admin → Trigger → New** — one trigger per event, each pointing to the webhook:
   - "New ticket" — condition: ticket state `new`, action: execute webhook with
     custom payload `{"event":"ticket_create","ticket_id":"#{ticket.id}"}`
   - "New customer article" — condition: article sender `Customer`, article created,
     payload `{"event":"article_create"}`
   - "SLA breach / escalation" — condition: escalation-at reached, payload
     `{"event":"sla_breach"}`

The relay reads `event` from the JSON body and maps to the waveform table above.
Unknown events are logged and ignored (no haptic, no 500).

## Open questions (confirm before implementation)

- [ ] **Scope filter**: all tickets, only assigned-to-me, or a specific group?
      Applied as a `condition` in each Zammad trigger.
- [ ] **Port 41500** acceptable? (HapticWeb uses 41443; staying in that range.)
- [ ] Windows Firewall rule scoped to `Private` profile only — confirm yes.
- [ ] Should the relay log events to a file (for troubleshooting misconfigured
      triggers) or keep it stateless?

## Out of scope (for now)

- TLS on the relay (LAN-only, HMAC gives integrity; TLS would need certs and complicates install).
- Retries / queueing if HapticWeb is down — the relay just logs the failure and continues.
- macOS/Linux parity — the relay itself is cross-platform Python, but `install.ps1`
  and the firewall step are Windows-only. macOS install would be a second plist.
