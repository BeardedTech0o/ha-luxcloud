# Security Policy

## Supported versions

| Version | Supported |
|:--------|:---------:|
| Latest release | ✅ |
| Previous releases | ❌ |

Only the latest release receives security fixes. Please update before reporting.

---

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report security issues by emailing the maintainer directly or by using [GitHub's private vulnerability reporting](https://github.com/BeardedTech0o/ha-luxcloud/security/advisories/new).

Include as much detail as possible:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

You can expect an acknowledgement within **72 hours** and a resolution or status update within **14 days**.

---

## Scope

This integration handles:

- **LuxPower cloud credentials** — stored in the Home Assistant config entry, protected by HA's credential storage. Passwords are hashed with MD5 before being sent to the LuxPower API (this is the API's own requirement).
- **Outbound HTTP requests** — made only to `openapi.luxpowertek.com` or `eu.luxpowertek.com`.
- **No inbound connections** — the integration does not open any ports or accept external connections.

---

## Out of scope

- Vulnerabilities in the LuxPower cloud API itself
- Issues requiring physical access to the inverter or local network
- Home Assistant core security issues (report those to the [HA security team](https://www.home-assistant.io/security/))
