# StudyBuddy 2.0 Product Requirements

**Status:** Proposed for Phase 1.0  
**Scope:** First usable version (MVP) of StudyBuddy 2.0  
**Last updated:** 2026-10-25

> **Document conventions**
> **Verified** means the behavior exists in the current Django application.  
> **Proposed** means planned work that is not implemented yet.

Related documents: [Architecture overview](../architecture/overview.md) · [Data model](../architecture/data-model.md) · [Roadmap](../development/roadmap.md)

## 1. Product vision

StudyBuddy helps learners turn isolated study into small, topic-focused communities. A user should be able to discover a relevant study room, understand its subject, and participate in a discussion without unnecessary setup.

StudyBuddy 2.0 is the first polished, production-oriented version of the product. It keeps the useful core of the existing application and delivers it through a maintainable React and Django API architecture.

### Target users

- **Independent learners** looking for a room about a specific subject.
- **Study group hosts** who want to create and manage a focused discussion space.
- **Casual visitors** who want to browse public discussions before registering.
- **Project staff** who manage content through Django administration.

### Product principles

1. **Low friction:** browsing should not require an account.
2. **Clear ownership:** hosts manage rooms; authors manage their messages.
3. **Public by default:** rooms are discoverable and readable by everyone.
4. **Simple before clever:** the MVP uses proven Django and React patterns, not distributed systems.
5. **Server-side trust:** the API enforces permissions; the UI only reflects them.
6. **Accessible and responsive:** core journeys work on mobile and desktop and with keyboard navigation.

## 2. MVP scope

### MVP features

- Account registration, login, and logout.
- Public room discovery, search, and topic filtering.
- Room detail pages with messages and participant lists.
- Room creation, editing, and deletion by the room host.
- Message creation by authenticated users.
- Message deletion by the message author.
- Public user profiles with hosted rooms and recent messages.
- Recent activity feed.
- Profile editing for the signed-in user.
- Django administration for staff data management.
- Responsive React interface backed by a versioned Django REST API.

### Explicit exclusions from the MVP

- Private, unlisted, or invite-only rooms.
- Direct messages.
- Real-time messaging or presence indicators.
- File or image attachments.
- Notifications, mentions, reactions, or message threading.
- Social login, email verification, and password reset.
- User account deletion, data export, or GDPR tooling.
- Custom moderation dashboards, reporting, or appeals.
- Full-text search, recommendations, or AI features.
- Mobile applications, desktop applications, or browser extensions.
- Organizations, teams, billing, or paid plans.
- Public developer API or third-party integrations.
- Internationalization beyond the current English interface.

These exclusions are deliberate scope controls, not statements that the features are unimportant.

### Delivery assumption

The product MVP is considered usable when the React application reaches feature parity with the current Django templates for the journeys below. The existing server-rendered application remains the behavioral reference until parity is verified.

## 3. User journeys

### Journey 1: Guest discovers a room

1. A visitor opens StudyBuddy and sees public study rooms.
2. The visitor searches by keyword or selects a topic.
3. The visitor opens a room and reads its messages.
4. The visitor attempts to post and is prompted to log in.

**Success:** the visitor can find and read relevant content without registering.

### Journey 2: New member joins a conversation

1. A new user registers with a username and password.
2. The user is signed in and returned to the application.
3. The user opens a room, writes a message, and submits it.
4. The message appears in the room and the user appears in the participant list.

**Success:** the user can register, authenticate, and post without administrative help.

### Journey 3: Host creates and manages a room

1. A signed-in user creates a room with a name, topic, and description.
2. The user becomes the room host.
3. The host edits the room later or deletes it after confirmation.
4. A different user cannot edit or delete the host's room.

**Success:** ownership rules are enforced by the API and reflected in the UI.

### Journey 4: Member manages their content

1. A signed-in user visits their profile or the activity feed.
2. The user edits their username or email.
3. The user deletes one of their own messages.
4. The user cannot delete another user's message.

**Success:** users can manage their own data without gaining control over other users' content.

### Journey 5: Unauthorized action is rejected

1. A user opens a direct room-edit or message-delete URL for content they do not own.
2. The API returns `403 Forbidden`.
3. The UI shows an appropriate error without exposing an edit or delete control.

**Success:** authorization is enforced on the server and is not merely hidden in the interface.

## 4. Roles and permissions

| Capability | Guest | Signed-in user | Room host | Staff |
|---|---|---|---|---|
| Browse rooms, topics, profiles, activity | Yes | Yes | Yes | Yes |
| Read room messages | Yes | Yes | Yes | Yes |
| Register, log in, log out | Yes | Yes | Yes | Yes |
| Create a room | No | Yes | Yes | Yes |
| Edit or delete a room | No | No | Own rooms | Via Django admin |
| Post a message | No | Yes | Yes | Yes |
| Delete a message | No | Own messages | Own messages | Via Django admin |
| Edit own profile | No | Yes | Yes | Yes |
| Manage topics or users | No | No | No | Via Django admin |

**Notes:**

- A user may host some rooms and participate in others.
- Room hosts do not gain permission to delete other users' messages in the MVP.
- Staff permissions in the application are limited to Django administration.

## 5. Functional requirements

Priority meanings: **Must** = required for MVP; **Should** = strongly desirable; **Could** = optional.

### Authentication and accounts

| ID | Requirement | Priority |
|---|---|---|
| AUTH-1 | A visitor can register with a unique username and password. | Must |
| AUTH-2 | Registration validates passwords using Django's configured validators. | Must |
| AUTH-3 | A registered user can log in and maintain a session. | Must |
| AUTH-4 | A signed-in user can log out, invalidating the session. | Must |
| AUTH-5 | Protected actions redirect or return an authentication error when the user is not signed in. | Must |
| AUTH-6 | Authentication errors are shown without revealing whether a username exists. | Should |
| AUTH-7 | A signed-in user can update their username and email address. | Must |
| AUTH-8 | Email addresses are not shown on public profiles. | Must |

### Rooms and discovery

| ID | Requirement | Priority |
|---|---|---|
| ROOM-1 | Anyone can view a paginated list of public rooms. | Must |
| ROOM-2 | Anyone can search rooms by name, description, or topic. | Must |
| ROOM-3 | Anyone can filter rooms by topic. | Must |
| ROOM-4 | Anyone can view a room's name, topic, host, description, messages, and participants. | Must |
| ROOM-5 | A signed-in user can create a room with a name, topic, and description. | Must |
| ROOM-6 | The creator becomes the room host. | Must |
| ROOM-7 | Only the host can edit or delete a room. | Must |
| ROOM-8 | Deleting a room requires explicit confirmation. | Must |
| ROOM-9 | Empty and no-result states are clearly presented. | Must |

### Messages and participation

| ID | Requirement | Priority |
|---|---|---|
| MSG-1 | A signed-in user can post a message in any public room. | Must |
| MSG-2 | Empty or whitespace-only messages are rejected. | Must |
| MSG-3 | Posting a message adds the author to the room's participant list. | Must |
| MSG-4 | Messages are displayed newest first, matching current behavior. | Must |
| MSG-5 | Only the message author can delete the message. | Must |
| MSG-6 | Deleting a message requires explicit confirmation. | Must |
| MSG-7 | Room hosts cannot delete other users' messages in the MVP. | Must |

### Profiles, topics, and activity

| ID | Requirement | Priority |
|---|---|---|
| PROF-1 | Anyone can view a public profile with username, hosted rooms, and messages. | Must |
| PROF-2 | A signed-in user can edit their own profile. | Must |
| TOPIC-1 | Anyone can browse topics and see room counts. | Must |
| TOPIC-2 | A topic can be selected or created while creating a room. | Must |
| TOPIC-3 | Public topic management is not exposed in the MVP; staff use Django admin. | Must |
| ACT-1 | Anyone can view a recent activity feed of room messages. | Must |
| ACT-2 | Activity entries link to the relevant room and author profile. | Should |

### Administration and UX

| ID | Requirement | Priority |
|---|---|---|
| ADM-1 | Staff can manage users, topics, rooms, and messages through Django admin. | Must |
| ADM-2 | The MVP does not include a custom moderation interface. | Must |
| UX-1 | Core journeys work at mobile, tablet, and desktop widths. | Must |
| UX-2 | Lists and forms provide loading, empty, success, and error states. | Must |
| UX-3 | Forms expose labels, validation messages, and keyboard-accessible controls. | Must |
| UX-4 | Destructive actions require confirmation. | Must |
| UX-5 | Signed-in and guest navigation states are visually distinct. | Must |

## 6. Non-functional requirements

| ID | Requirement | Priority |
|---|---|---|
| SEC-1 | Authorization is enforced on the server for every protected operation. | Must |
| SEC-2 | Cookie-authenticated unsafe requests require CSRF protection. | Must |
| SEC-3 | Passwords are hashed using Django's password framework. | Must |
| SEC-4 | Secrets are supplied through environment variables and are never committed. | Must |
| SEC-5 | Public API responses do not expose email addresses or password data. | Must |
| SEC-6 | Authentication endpoints have basic abuse protection before public launch. | Should |
| PRIV-1 | Public content is clearly identified as public; email remains private. | Must |
| PERF-1 | List endpoints are paginated and avoid unbounded responses. | Must |
| PERF-2 | Core pages remain responsive on a typical broadband connection. | Should |
| A11Y-1 | Core journeys meet WCAG 2.1 AA basics: labels, focus, contrast, and keyboard use. | Must |
| A11Y-2 | Color is not the only way to communicate state. | Should |
| REL-1 | Database changes are applied through reviewed migrations with a backup plan. | Must |
| REL-2 | Failed requests show recoverable errors rather than blank screens. | Must |
| MAINT-1 | Critical backend and frontend behavior is covered by automated tests. | Must |
| MAINT-2 | API contracts and environment configuration are documented. | Must |
| COMPAT-1 | The interface supports current versions of Chrome, Firefox, Edge, and Safari. | Should |
| OBS-1 | Production errors and key events are observable through logs or error tracking. | Should |

## 7. Definition of MVP completion

The MVP is complete when all of the following are true:

1. Every **Must** requirement is implemented and demonstrated through the primary user journeys.
2. Backend tests, frontend tests, and end-to-end tests for the critical journeys pass in CI.
3. The permissions matrix is verified by automated tests for guest, member, host, and non-owner access.
4. No critical or high-severity security findings remain in the authentication and authorization flows.
5. Core pages are usable at 375px, 768px, and desktop widths.
6. Accessibility checks cover keyboard navigation, form labels, focus visibility, and basic contrast.
7. A clean environment can be configured from the documentation and run against a fresh database.
8. The React application reaches feature parity with the existing server-rendered application for the MVP scope.
9. Existing data is preserved during the transition, and the database migration path is documented.
10. The team can demonstrate creating a room, posting a message, editing a profile, and rejecting an unauthorized action end to end.

Public launch has additional gates: production database, HTTPS, secure cookies, backups, monitoring, and account-recovery decisions. Those are covered in the roadmap.

## 8. Assumptions and open questions

**Assumptions**

- Public room browsing remains available to guests.
- Email addresses are optional and are never displayed publicly.
- Room participants are recorded implicitly when a user posts; there is no explicit join/leave workflow in the MVP.
- Room names do not need to be unique.
- Staff use Django admin for moderation and data management.
- The MVP remains English-only.

**Open questions**

- Is password reset required for the first public launch, or can it follow a controlled beta?
- Is email verification required before public launch?
- Should room hosts eventually be able to moderate messages, or should moderation remain staff-only?
- Is a separate profile entity needed, or are Django `User` fields sufficient for the MVP?
- What deployment provider and domain will be used?
- What data-retention and account-deletion policy is required before accepting public users?

These questions should be resolved before the release-readiness phase, not during the first API implementation.
