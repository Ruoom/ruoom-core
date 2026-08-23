# Ruoom email template contract

The email shell is owned by `ruoom/automated_email_system.py`. It is the single source of truth for the card, header, footer, responsive behavior, typography, and business branding.

Current transactional templates under this directory are content fragments. They must:

- omit `<html>`, `<head>`, and `<body>` wrappers;
- use the shared semantic classes such as `email-eyebrow`, `email-panel`, `email-detail-table`, `email-button`, and `email-note`;
- avoid hard-coded brand colors, gradients, logo headers, and footer shells;
- accept business-specific styling through the shared renderer and `business_id`.

Plugin packages own their content fragments (for example, payment owns `emails/transaction-receipt.html`, digitalproducts owns `emails/digital-good-alert.html`, and email_otp owns `email_otp/emails/code.html`). They should render those fragments and pass the result to `automated_email_send`; they must not copy or override the shared shell. This keeps plugin behavior with the plugin while core branding updates apply consistently across every plugin email.

Some historical, unreferenced sample templates remain in this directory for compatibility. Do not add new send paths to those files; migrate any revived template to the fragment contract first.
