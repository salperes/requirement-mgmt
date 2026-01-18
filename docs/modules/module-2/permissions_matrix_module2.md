# Permissions Matrix — Module-2 Additions

## New Permissions
- req:comment:create
- req:comment:edit
- req:comment:delete
- req:status:change
- req:approve
- notif:read
- notif:mark_read

## Matrix
| Permission | Admin | Owner | Reviewer | Approver | Viewer |
|---|---:|---:|---:|---:|---:|
| req:comment:create | ✅ | ✅ | ✅ | ✅ | ❌ |
| req:comment:edit | ✅ | ✅ (own) | ✅ (own) | ✅ (own) | ❌ |
| req:comment:delete | ✅ | ✅ (own) | ✅ (own) | ✅ (own) | ❌ |
| req:status:change | ✅ | ✅ | ✅ | ✅ | ❌ |
| req:approve | ✅ | ❌ | ❌ | ✅ | ❌ |
| notif:read | ✅ | ✅ | ✅ | ✅ | ✅ |
| notif:mark_read | ✅ | ✅ | ✅ | ✅ | ✅ |

Notes:
- "(own)" means the actor can only edit/delete comments they authored.
