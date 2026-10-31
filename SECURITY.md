# Security Policy

## Supported Versions

Security fixes are made for the latest release of izaya.

## Reporting a Vulnerability

Please don't report security problems in a public issue. Use GitHub's private
[vulnerability reporting](https://github.com/Metron-Project/izaya/security/advisories/new) instead,
and include the steps to reproduce the problem and the izaya and Django versions affected.

## Protecting Private Data

Search endpoints are public unless a lookup's `has_access` says otherwise, and a per-user
`get_queryset` doesn't limit what a form accepts or renders. See
[Private data](README.md#private-data) in the README for how to restrict a lookup and its form field.
