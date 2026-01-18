# API Contract — Module-3

## Links
- POST /links
- DELETE /links/{id}
- GET /links?source_type=&source_id=&target_type=&target_id=&link_type=

## RTM
- GET /rtm?baseline_id=&format=json|csv|md&discipline=&type=&suspect=

## Impact
- GET /requirements/{id}/impact

## Orphans
- GET /orphans?entity_type=Test|Design|Standard
  - Returns orphan entities by type (current implementation returns Test orphans; Design/Standard placeholders)

## Suspect Override
- POST /suspect/{entity_type}/{entity_id}/clear