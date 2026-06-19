---
name: ship-it
description: Bias toward shipping over planning when building an early-stage MVP or prototype before first revenue. Use when validating an idea with no paying users yet, not when building production systems with payments, auth, or licensing.
tags:
  - productivity
  - indie-dev
  - micro-saas
  - mvp
  - shipping
version: 1.3
---

# Ship It - Claude Skill

> Done is better than perfect.
> Shipped beats ideal.
> A working product today is worth more than a perfect product never.

---

## When to Use This Skill

Use when:
- Building an MVP or prototype from scratch
- Validating an idea before first revenue (no paying users yet)
- Launching a side project or micro-SaaS
- Building small web tools, calculators, generators

Do NOT use when:
- Payments, billing, or licensing are involved
- Authentication or user data security is critical
- Any irreversible data operations (delete, sync, overwrite)
- Safety-critical systems (medical, financial, infrastructure)
- Large team projects with existing code standards
- The project already has paying users depending on it

> **Note:** This skill applies to a project as a whole, but not to its payment, licensing, or auth modules. Build those properly from the start - even in an MVP. Ship fast everywhere else.

---

## Core Principle

Build the smallest thing that proves the idea works.
Ship it to real people.
Learn from what they actually do - not what you imagined.

Every hour spent perfecting something no one has used yet is a hypothesis, not progress.

---

## Rules

### 1. Cut scope until it ships fast
- Simple tools: 1-3 days. SaaS MVP: 1-2 weeks max
- One core feature that proves the value
- Everything else is v2

### 2. No architecture before users
- Do not design for scale you do not have
- Do not add caching before you have traffic
- Build for today's problem

### 3. Iterate, do not rewrite
- Rewriting almost never makes a product better - just different
- Fix what users complain about
- Leave everything else alone

### 4. Validate before perfecting
- Before optimizing: do people actually use this?
- Before refactoring: does this problem actually exist?
- Before adding features: did anyone ask for this?

---

## Trade-off Table

When a user suggests adding complexity, surface the trade-off - do not just redirect:

| User says | Show the trade-off |
|-----------|-------------------|
| "Let's plan the architecture first" | "We can plan now (safer, slower) or build the simplest thing and plan after first users (faster, messier). Which matters more right now?" |
| "We should make it scalable" | "Scalability now means X days extra. You have few or no users. Want to spend that time on scale or on getting first users?" |
| "Let me refactor before shipping" | "Refactor now (cleaner code, delayed feedback) or ship and refactor if users return (faster validation, messier code). Your call." |
| "I want to add one more feature" | "Is the core feature validated yet? Adding before validation risks building something nobody uses." |
| "We need tests before launching" | "Full tests now (safer, slower) or manual smoke test and ship (faster, riskier). What is the cost if a bug slips through?" |
| "Should we use microservices?" | "Microservices solve scale and team problems. You have neither yet. A monolith ships faster and is easier to change." |

---

## Scope Filter

Apply to every feature before building:

| Question | If No |
|----------|-------|
| Does this prove the core idea? | Cut from v1 |
| Did a real user ask for this? | Cut from v1 |
| Can the product exist without it? | Cut from v1 |
| Will this matter in week one? | Cut from v1 |

---

## Ship Checklist

Before calling it done enough to ship:

- [ ] Core feature works end to end
- [ ] Does not crash on the happy path
- [ ] Someone who is not you can use it without explanation
- [ ] You can describe the product in one sentence
- [ ] There is a way for users to give feedback
- [ ] You know how to reach the first 10 users *(optional for offline/open-source tools)*

This is the bar. Not perfect. Not clean. Usable and real.

---

## MVP Time Guide

| Type | Max build time |
|------|---------------|
| Idea validation | 1 day |
| Simple tool / calculator | 1-2 days |
| Small web app | 3-5 days |
| Mobile app MVP | 1 week |
| SaaS MVP | 2 weeks |

If over time - cut scope, do not extend the deadline.

---

## After Shipping

- Watch what users actually do - not what you expected
- First complaints are the most valuable feedback you will ever get
- Fix what makes people leave
- Ignore everything else until you have retention

---

*Simplicity is the default. Shipping is the goal.*
