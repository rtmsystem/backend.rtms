# Specification: Matches Management System

## 📋 Context and Objective

Create a new Django app called `matches` to manage matches (encounters) within tournament divisions. The system must allow recording points and match results, supporting both singles and doubles matches.

---

## 🎯 Functionality Scope

### 1. Data Models

#### `Match` Model
- **Relationships:**
  - `division` (ForeignKey to `TournamentDivision`, related_name='matches') - Division where the match is played
  - `match_code` (CharField, max_length=20) - **Unique match code per division**: M1, M2, M3, LM1, LM2, etc.
  - `player1` (ForeignKey to `PlayerProfile`, nullable) - Player 1 or Team 1 (player 1 in singles/doubles). NULL for byes
  - `player2` (ForeignKey to `PlayerProfile`, nullable) - Player 2 in singles (optional). NULL for byes
  - `partner1` (ForeignKey to `PlayerProfile`, nullable) - Player 1's partner (for doubles)
  - `partner2` (ForeignKey to `PlayerProfile`, nullable) - Player 2's partner (for doubles)
  - `created_by` (ForeignKey to `User`, nullable) - User who created the match
  - `next_match` (ForeignKey to 'self', nullable, related_name='previous_matches') - Next match in the bracket

- **Status Fields:**
  - `match_type` (CharField with choices: `SINGLES`, `DOUBLES`) - Match type
  - `status` (CharField with choices: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`) - Match status
  - `winner` (ForeignKey to `PlayerProfile`, nullable) - Match winner (player or team)
  - `winner_partner` (ForeignKey to `PlayerProfile`, nullable) - Winning partner (for doubles)
  - `round_number` (PositiveIntegerField, nullable) - Round number in the bracket
  - `is_losers_bracket` (BooleanField, default=False) - Indicates if it is in the losers bracket
  - `scheduled_at` (DateTimeField, nullable) - Scheduled date and time of the match
  - `started_at` (DateTimeField, nullable) - Actual start date and time
  - `completed_at` (DateTimeField, nullable) - Completion date and time

- **Match Configuration (CONFIGURABLE):**
  - `max_sets` (PositiveIntegerField, default=5) - **Maximum number of sets** (3-10)
  - `points_per_set` (PositiveIntegerField, default=15) - **Points needed per set** (1-50)

- **Metadata:**
  - `created_at` (DateTimeField) - Creation date
  - `updated_at` (DateTimeField) - Last update date
  - `notes` (TextField, blank) - Additional notes about the match

- **Indexes and Constraints:**
  - `match_code` must be unique per division (use `unique_together` with `division`)

#### `Set` Model
- **Relationship:**
  - `match` (ForeignKey to `Match`, related_name='sets') - Match it belongs to

- **Fields:**
  - `set_number` (PositiveIntegerField) - Set number (dynamic according to `match.max_sets`)
  - `player1_score` (PositiveIntegerField, default=0) - Player/Team 1 points
  - `player2_score` (PositiveIntegerField, default=0) - Player/Team 2 points
  - `winner` (CharField with choices: `PLAYER1`, `PLAYER2`, nullable) - Set winner
  - `completed_at` (DateTimeField, nullable) - Set completion date

- **Validations:**
  - `set_number` must be unique per match and not exceed `match.max_sets`
  - The winner must have score >= `match.points_per_set`

---

## 📐 Business Rules

### Match Format (CONFIGURABLE)
- **Default:** Maximum 5 sets of 15 points each are played
- **Configurable:** When creating a match, can specify:
  - `max_sets`: Number of sets (3-10, default: 5)
  - `points_per_set`: Points needed per set (1-50, default: 15)
- **Victory Rule:** The first to win `(max_sets // 2) + 1` sets wins the match
  - Example: 5 sets = 3 sets to win, 7 sets = 4 sets to win
- **Scoring Format:** Each set requires `points_per_set` points to win
- **Sets:** Up to `max_sets` sets can be played, but the match ends when a player/team reaches the necessary sets to win

### Match Types

#### Singles
- `player1` = Player 1
- `player2` = Player 2
- `partner1` = NULL
- `partner2` = NULL
- `match_type` = `SINGLES`

#### Doubles
- `player1` = Player 1 of Team 1
- `partner1` = Player 2 of Team 1
- `player2` = Player 1 of Team 2
- `partner2` = Player 2 of Team 2
- `match_type` = `DOUBLES`

### Match Code System
- **Winners Bracket:** M1, M2, M3, M4, ... (Match 1, Match 2, etc.)
- **Losers Bracket:** LM1, LM2, LM3, ... (Lost Match 1, Lost Match 2, etc.)
- Codes are unique per division (not globally)
- Generated sequentially when creating the bracket

### Validations
1. Players must be approved (`status=APPROVED`) in the corresponding division
2. In doubles, both players of the team must be in the division
3. Matches cannot be created for unpublished divisions
4. The winner can only be established when the match reaches the necessary sets: `(max_sets // 2) + 1`
5. Each set must have a winner (player1_score or player2_score >= `points_per_set`)
6. `match_code` must be unique per division
7. Matches can have `player1` or `player2` NULL to represent byes

---

## 🔧 Required Services

### 1. `MatchCreationService`
**Responsibility:** Create a new match with business validations

**Parameters:**
- `division_id` (int) - Division ID
- `match_code` (str) - Unique match code (M1, M2, LM1, etc.)
- `player1_id` (int, optional) - Player 1 ID (can be NULL for byes)
- `player2_id` (int, optional) - Player 2 ID (can be NULL for byes)
- `partner1_id` (int, optional) - Partner 1 ID (doubles)
- `partner2_id` (int, optional) - Partner 2 ID (doubles)
- `match_type` (str) - `SINGLES` or `DOUBLES`
- `max_sets` (int, default=5) - **Number of sets** (3-10)
- `points_per_set` (int, default=15) - **Points per set** (1-50)
- `round_number` (int, optional) - Round number
- `is_losers_bracket` (bool, default=False) - If in losers bracket
- `next_match_id` (int, optional) - Next match ID in bracket
- `scheduled_at` (datetime, optional) - Scheduled date
- `user` (User) - User creating the match

**Validations:**
- Division must exist and be published
- `match_code` unique in division
- Players must be approved in the division (or allow NULL for byes)
- In doubles, validate both players of the team are approved
- Validate no duplicate match between the same players
- Validate ranges: `max_sets` (3-10), `points_per_set` (1-50)

**Returns:** `Match` instance

### 2. `MatchUpdateService`
**Responsibility:** Update an existing match

**Parameters:**
- `match_id` (int)
- `data` (dict) - Data to update
- `user` (User)

**Validations:**
- Match must exist
- Cannot modify a completed match without special permissions
- Validate status changes (valid transitions)

**Returns:** Updated `Match` instance

### 3. `MatchDeletionService`
**Responsibility:** Delete a match

**Parameters:**
- `match_id` (int)
- `user` (User)

**Validations:**
- Match must exist
- Can only delete pending or cancelled matches
- Verify user permissions

**Returns:** None

### 4. `MatchListService`
**Responsibility:** Get list of matches with filters

**Parameters:**
- `division_id` (int, optional)
- `tournament_id` (int, optional)
- `match_type` (str, optional)
- `status` (str, optional)
- `player_id` (int, optional)

**Returns:** `Match` QuerySet with optimizations (select_related, prefetch_related)

### 5. `MatchBracketGenerationService` (REPLACES MatchRandomGenerationService)
**Responsibility:** Generate all matches of the complete bracket according to division format

**Parameters:**
- `division_id` (int)
- `max_sets` (int, optional, default=5)
- `points_per_set` (int, optional, default=15)
- `user` (User)

**Logic for SINGLE ELIMINATION (KNOCKOUT):**
1. Get all approved involvements of the division
2. Randomize participant order
3. Calculate number of rounds needed: `ceil(log2(participants))`
4. Create first round matches:
   - If odd number, some participants get a bye (no opponent)
   - Create matches with codes: M1, M2, M3, M4, etc.
   - `round_number = 1`, `is_losers_bracket = False`
5. Create subsequent round matches:
   - Winners of previous round advance
   - Create matches with sequential codes
   - Connect with `next_match` to the previous round match
   - Increment `round_number`
6. Create final: A single final match (last round)
7. All matches in `PENDING` state, except those with bye (can be marked as completed with automatic winner)

**Logic for DOUBLE ELIMINATION (DOUBLE_SLASH):**
1. Get all approved involvements
2. Randomize order
3. Create main bracket (Winners Bracket):
   - Similar to Single Elimination
   - Codes: M1, M2, M3, etc.
   - `is_losers_bracket = False`
   - Connect matches with `next_match`
4. Create losers bracket (Losers Bracket):
   - Losers from main bracket go to losers bracket
   - Codes: LM1, LM2, LM3, etc. (Lost Match)
   - `is_losers_bracket = True`
   - Create all necessary rounds
   - Winners advance and losers are eliminated
5. Create Grand Final:
   - Between Winners Bracket winner and Losers Bracket winner
   - If Losers Bracket winner wins, a second match is played (Bracket Reset)
6. Connect matches with `next_match` appropriately in both brackets

**Validations:**
- Division must exist and be published
- Minimum 2 approved players/pairs
- Verify division format: `division.format` must be `KNOCKOUT` or `DOUBLE_SLASH`
- Do not create brackets if matches already exist for the division (or delete existing ones first with confirmation)
- Validate that `max_sets` and `points_per_set` are in valid ranges

**Returns:** List of `Match` instances created, organized by round and bracket

### 6. `MatchScoreService`
**Responsibility:** Register/update set results and determine winner

**Parameters:**
- `match_id` (int)
- `sets_data` (list) - List of dictionaries with set data:
  ```python
  [
    {
      'set_number': 1,
      'player1_score': 15,
      'player2_score': 12
    },
    # ... more sets
  ]
  ```
- `user` (User)

**Logic:**
1. Validate match exists and is not completed
2. Get `max_sets` and `points_per_set` from match
3. For each set:
   - Create or update Set
   - Determine set winner (highest score >= `points_per_set`)
   - Validate score is valid (>= 0, winner >= `points_per_set`)
   - Validate `set_number` does not exceed `max_sets`
4. Count sets won by each side
5. Calculate sets needed to win: `sets_to_win = (max_sets // 2) + 1`
   - Example: 5 sets = 3 to win, 7 sets = 4 to win
6. If any player/team has `sets_to_win` sets won:
   - Set `winner` (and `winner_partner` if doubles) of match
   - Change status to `COMPLETED`
   - Set `completed_at`
   - If has `next_match`, update the next match with the winner automatically

**Returns:** Updated `Match` instance

---

## 🌐 API Endpoints

### Base URL: `/api/v1/matches/`

### 1. List Matches
- **Method:** `GET /api/v1/matches/`
- **Authentication:** Optional (public to view, authenticated to create)
- **Query Parameters:**
  - `division_id` (int, optional)
  - `tournament_id` (int, optional)
  - `match_type` (str, optional)
  - `status` (str, optional)
  - `player_id` (int, optional)
  - `page` (int, optional)
  - `page_size` (int, optional)
- **Response:** Paginated list of matches with sets included

### 2. Create Match
- **Method:** `POST /api/v1/matches/`
- **Authentication:** Required
- **Body:**
  ```json
  {
    "division_id": 1,
    "match_type": "SINGLES",
    "player1_id": 1,
    "player2_id": 2,
    "scheduled_at": "2025-12-01T10:00:00Z",
    "notes": "Quarterfinal match"
  }
  ```
- **Response:** Created match with code 201

### 3. Get Match
- **Method:** `GET /api/v1/matches/{id}/`
- **Authentication:** Optional
- **Response:** Match detail with sets

### 4. Update Match
- **Method:** `PUT /api/v1/matches/{id}/` or `PATCH /api/v1/matches/{id}/`
- **Authentication:** Required
- **Body:** Fields to update
- **Response:** Updated match

### 5. Delete Match
- **Method:** `DELETE /api/v1/matches/{id}/`
- **Authentication:** Required
- **Response:** 204 No Content

### 6. Register Results
- **Method:** `POST /api/v1/matches/{id}/scores/`
- **Authentication:** Required
- **Body:**
  ```json
  {
    "sets": [
      {
        "set_number": 1,
        "player1_score": 15,
        "player2_score": 12
      },
      ...
    ]
  }
  ```
- **Response:** Updated match with results

### 7. Generate Complete Bracket
- **Method:** `POST /api/v1/matches/generate-bracket/`
- **Authentication:** Required
- **Body:**
  ```json
  {
    "division_id": 1,
    "max_sets": 5,        // Optional, default: 5
    "points_per_set": 15  // Optional, default: 15
  }
  ```
- **Description:** Generates ALL bracket matches according to division format:
  - **Single Elimination (KNOCKOUT):** Creates matches M1, M2, M3... up to final
  - **Double Elimination (DOUBLE_SLASH):** Creates matches M1-Mn (winners) and LM1-LMn (losers)
- **Response:** List of created matches grouped by round (201 Created)

---

## 📁 File Structure

```
apps/matches/
├── __init__.py
├── models.py              # Match, Set models
├── serializers.py         # MatchReadSerializer, MatchWriteSerializer, SetSerializer, etc.
├── views.py              # MatchViewSet, custom endpoints
├── urls.py               # URL routing
├── services.py           # All mentioned services
├── validators.py         # Business validators
├── permissions.py        # Custom permissions
├── exceptions.py         # Exceptions with error_code
├── constants.py          # Constants and choices
├── admin.py              # Django Admin
├── apps.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_validators.py
    └── test_views.py
```

---

## ✅ Implementation Checklist

### Models
- [ ] Create `Match` model with all fields and relationships
- [ ] Create `Set` model with relationship to `Match`
- [ ] Add validations in `clean()` methods of models
- [ ] Create utility methods in models (e.g., `get_sets_won_by_player1()`)
- [ ] Add appropriate indexes in Meta
- [ ] Create migrations

### Serializers
- [ ] `MatchReadSerializer` - For reading (includes sets, player names)
- [ ] `MatchWriteSerializer` - For creation/update
- [ ] `MatchListSerializer` - Optimized for listing
- [ ] `SetSerializer` - For individual sets
- [ ] `MatchScoreSerializer` - For score registration

### Services
- [ ] `MatchCreationService` with validations
- [ ] `MatchUpdateService` with validations
- [ ] `MatchDeletionService` with validations
- [ ] `MatchListService` with optimized filters
- [ ] `MatchBracketGenerationService` with generation algorithm
- [ ] `MatchScoreService` with winner calculation logic

### Exceptions
- [ ] `MatchBusinessError` (base)
- [ ] `DivisionNotPublishedError`
- [ ] `PlayerNotApprovedError`
- [ ] `DuplicateMatchError`
- [ ] `MatchAlreadyCompletedError`
- [ ] `InvalidScoreError`
- [ ] All with `error_code` for i18n

### Validators
- [ ] Validate approved players in division
- [ ] Validate set format (5 sets max, 15 points)
- [ ] Validate no duplicate matches
- [ ] Validate status transitions

### Views
- [ ] `MatchViewSet` with CRUD actions
- [ ] Endpoint `POST /matches/{id}/scores/` to register results
- [ ] Endpoint `POST /matches/generate-bracket/` to generate matches
- [ ] Use `StandardResponseMixin` for responses
- [ ] Handle exceptions and return `error_code`

### Permissions
- [ ] View matches: Public or authenticated
- [ ] Create/edit/delete: Tournament organization admins only
- [ ] Register results: Admins or involved players

### URLs
- [ ] Register URLs in `config/urls.py`
- [ ] Include in API versioning (`/api/v1/`)

### Tests
- [ ] Tests for models
- [ ] Tests for services (success and error cases)
- [ ] Tests for validators
- [ ] Tests for views (integration)
- [ ] Tests for bracket generation

### Admin
- [ ] Register models in admin
- [ ] Configure list_display, list_filter, search_fields

---

## 🎨 Design Considerations

1. **Query Optimization:**
   - Use `select_related()` for division, tournament, players
   - Use `prefetch_related()` for sets
   - Create indexes on frequent search fields

2. **Transactions:**
   - Use `@transaction.atomic` in services modifying multiple objects
   - Especially in `MatchBracketGenerationService` and `MatchScoreService`

3. **Logging:**
   - Log match creation, update and deletion
   - Log important status changes

4. **Error Codes:**
   - All business errors must have unique `error_code`
   - Format: `ERROR_<DESCRIPTIVE_NAME>` or `MATCH_<ACTION>_<CONDITION>`

---

## 📝 Additional Notes

- Random generation must be deterministic (use seed) or completely random as per requirement
- Consider match limits per division to avoid overload
- Matches can have `CANCELLED` status if not played
- Consider adding `court` or `venue` field for match location (future)

---

**Author:** Tournament Management System  
**Date:** 2025-01-XX  
**Version:** 1.0
