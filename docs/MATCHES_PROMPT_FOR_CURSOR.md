# Cursor Prompt: Create Matches Management App (Matches)

## Main Instruction

Create a new Django app called `matches` to manage matches (encounters) in tournament divisions. Follow the project's clean architecture and all established conventions.

---

## 1. CREATE THE APP AND BASE STRUCTURE

1. Create the `matches` app in `apps/matches/`
2. Follow the standard project file structure:
   - `models.py`, `serializers.py`, `views.py`, `urls.py`
   - `services.py`, `validators.py`, `permissions.py`, `exceptions.py`, `constants.py`
   - `admin.py`, `apps.py`
   - `tests/` folder with structured tests

---

## 2. MODELS

### `Match` Model

**Fields:**
- `division` (ForeignKey to `TournamentDivision`, related_name='matches')
- `match_code` (CharField, max_length=20, unique=False) - Match code: M1, M2, M3, LM1, LM2, etc.
- `player1` (ForeignKey to `PlayerProfile`, related_name='matches_as_player1', nullable) - Can be NULL for byes
- `player2` (ForeignKey to `PlayerProfile`, nullable, related_name='matches_as_player2') - For singles, NULL for byes
- `partner1` (ForeignKey to `PlayerProfile`, nullable, related_name='matches_as_partner1') - For doubles
- `partner2` (ForeignKey to `PlayerProfile`, nullable, related_name='matches_as_partner2') - For doubles
- `match_type` (CharField, choices: `SINGLES`, `DOUBLES`)
- `status` (CharField, choices: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
- `winner` (ForeignKey to `PlayerProfile`, nullable, related_name='matches_won')
- `winner_partner` (ForeignKey to `PlayerProfile`, nullable, related_name='matches_won_as_partner') - For doubles
- `max_sets` (PositiveIntegerField, default=5) - **NEW: Configurable number of sets**
- `points_per_set` (PositiveIntegerField, default=15) - **NEW: Configurable points per set**
- `round_number` (PositiveIntegerField, nullable) - Round number in the bracket
- `is_losers_bracket` (BooleanField, default=False) - Indicates if it is in the losers bracket
- `next_match` (ForeignKey to 'self', nullable, related_name='previous_matches') - Next match in the bracket
- `scheduled_at` (DateTimeField, nullable)
- `started_at` (DateTimeField, nullable)
- `completed_at` (DateTimeField, nullable)
- `created_by` (ForeignKey to `User`, nullable)
- `notes` (TextField, blank=True)
- `created_at`, `updated_at` (standard timestamps)

**Validations:**
- In `clean()`: Validate that players are approved in the division
- Validate that the division is published
- Validate singles vs doubles logic
- Validate `max_sets` is >= 3 and <= 10
- Validate `points_per_set` is >= 1 and <= 50
- `match_code` must be unique per division (not globally)

### `Set` Model

**Fields:**
- `match` (ForeignKey to `Match`, related_name='sets')
- `set_number` (PositiveIntegerField, validators: min_value=1)
- `player1_score` (PositiveIntegerField, default=0)
- `player2_score` (PositiveIntegerField, default=0)
- `winner` (CharField, choices: `PLAYER1`, `PLAYER2`, nullable)
- `completed_at` (DateTimeField, nullable)

**Validations:**
- `set_number` must be unique per match
- In `clean()`: Validate that the winner has score >= `match.points_per_set`
- Set number cannot exceed `match.max_sets`

**Choices in `constants.py`:**
```python
class MatchType(models.TextChoices):
    SINGLES = 'singles', 'Singles'
    DOUBLES = 'doubles', 'Doubles'

class MatchStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

class SetWinner(models.TextChoices):
    PLAYER1 = 'player1', 'Player 1'
    PLAYER2 = 'player2', 'Player 2'
```

---

## 3. EXCEPTIONS (with error_code for i18n)

In `exceptions.py`:

```python
class MatchBusinessError(ValidationError):
    """Base exception with error_code"""
    def __init__(self, message: str, error_code: str, errors: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.message = message
        super().__init__(message)
        if errors:
            self.error_dict = errors

class DivisionNotPublishedError(MatchBusinessError):
    error_code = "ERROR_DIVISION_NOT_PUBLISHED"

class PlayerNotApprovedError(MatchBusinessError):
    error_code = "ERROR_PLAYER_NOT_APPROVED"

class DuplicateMatchError(MatchBusinessError):
    error_code = "ERROR_DUPLICATE_MATCH"

class MatchAlreadyCompletedError(MatchBusinessError):
    error_code = "ERROR_MATCH_ALREADY_COMPLETED"

class InvalidScoreError(MatchBusinessError):
    error_code = "ERROR_INVALID_SCORE"

class InsufficientPlayersError(MatchBusinessError):
    error_code = "ERROR_INSUFFICIENT_PLAYERS_FOR_GENERATION"
```

---

## 4. SERVICES

### `MatchCreationService`
**Responsibility:** Create a new single match with validations

**Parameters:**
- `division_id` (int)
- `player1_id` (int, optional) - Can be NULL for bye
- `player2_id` (int, optional) - Can be NULL for bye
- `partner1_id` (int, optional) - For doubles
- `partner2_id` (int, optional) - For doubles
- `match_type` (str) - `SINGLES` or `DOUBLES`
- `match_code` (str) - Unique match code (M1, M2, LM1, etc.)
- `max_sets` (int, default=5) - **NEW: Number of sets**
- `points_per_set` (int, default=15) - **NEW: Points per set**
- `round_number` (int, optional) - Round number
- `is_losers_bracket` (bool, default=False)
- `next_match_id` (int, optional) - Next match ID
- `scheduled_at` (datetime, optional)
- `user` (User)

**Validations:**
- Published division
- Approved players in division (or allow NULL for byes)
- `match_code` unique in division
- Validate logic singles vs doubles
- Validate ranges of `max_sets` (3-10) and `points_per_set` (1-50)
- Create match in atomic transaction

### `MatchUpdateService`
- Validate existence
- Validate valid status transitions
- Do not allow modifying completed matches (without special permission)

### `MatchDeletionService`
- Only delete pending or cancelled matches
- Validate permissions

### `MatchListService`
**Responsibility:** Get list of matches with advanced filters

**Parameters:**
- `division_id` (int, optional)
- `tournament_id` (int, optional)
- `match_type` (str, optional)
- `status` (str, optional)
- `player_id` (int, optional)
- `round_number` (int, optional) - **NEW: Filter by round**
- `is_losers_bracket` (bool, optional) - **NEW: Filter by bracket type**
- `match_code` (str, optional) - **NEW: Search by code**

**Returns:** Optimized QuerySet with `select_related()` and `prefetch_related()`

### `MatchBracketGenerationService` (REPLACES MatchRandomGenerationService)
**Responsibility:** Generate all matches of the complete bracket according to division format

**Parameters:**
- `division_id` (int) - Division ID
- `max_sets` (int, optional, default=5) - Number of sets per match
- `points_per_set` (int, optional, default=15) - Points per set
- `user` (User) - User generating the brackets

**Algorithm for SINGLE ELIMINATION (Knockout):**
1. Get all approved involvements of the division
2. Randomize participant order
3. Calculate number of rounds needed (log2 of participants, rounded up)
4. Create first round matches:
   - If odd number, some participants get a bye (no opponent)
   - Create matches with codes: M1, M2, M3, M4, etc.
   - `round_number = 1`
5. Create subsequent round matches:
   - Winners of previous round advance
   - Create matches with sequential codes
   - Connect with `next_match` to the previous round match
6. Create final: A single final match
7. All matches in `PENDING` state, except those with bye (can be marked as completed with automatic winner)

**Algorithm for DOUBLE ELIMINATION:**
1. Get all approved involvements
2. Randomize order
3. Create main bracket (Winners Bracket):
   - Similar to Single Elimination
   - Codes: M1, M2, M3, etc.
   - `is_losers_bracket = False`
4. Create losers bracket (Losers Bracket):
   - Losers from main bracket go to losers bracket
   - Codes: LM1, LM2, LM3, etc. (Lost Match)
   - `is_losers_bracket = True`
   - Create all necessary rounds
5. Create Grand Final:
   - Between Winners Bracket winner and Losers Bracket winner
   - If Losers Bracket winner wins, a second match is played (Bracket Reset)
6. Connect matches with `next_match` appropriately

**Validations:**
- Division must exist and be published
- Minimum 2 approved players/pairs
- Verify division format: `division.format` must be `KNOCKOUT` or `DOUBLE_SLASH`
- Do not create brackets if matches already exist for the division (or delete existing ones first)

**Returns:** List of created `Match` instances, organized by round

### `MatchScoreService`
**Responsibility:** Register/update set results and determine match winner

**Parameters:**
- `match_id` (int) - Match ID
- `sets_data` (list) - List of dictionaries with set data
- `user` (User) - User registering

**Logic:**
1. Validate match exists and is not completed
2. Get `max_sets` and `points_per_set` from match (configurable per match)
3. For each set:
   - Create or update Set
   - Determine set winner (highest score >= `points_per_set`)
   - Validate score is valid
4. Count sets won by each side
5. Calculate sets needed to win: `(max_sets // 2) + 1` (e.g., for 5 sets, you need 3)
6. If any player/team has enough sets to win:
   - Set `winner` (and `winner_partner` if doubles)
   - Change status to `COMPLETED`
   - Set `completed_at`
   - If has `next_match`, update the next match with the winner

**Returns:** Updated `Match` instance

---

## 5. SERIALIZERS

- `MatchReadSerializer`: Includes sets, player names, division, tournament, match_code, set configuration
- `MatchWriteSerializer`: For create/update (includes max_sets, points_per_set, match_code)
- `MatchListSerializer`: Optimized for listing (includes match_code, round_number)
- `SetSerializer`: For individual sets
- `MatchScoreSerializer`: For score registration endpoint
- `BracketGenerationSerializer`: For bracket generation endpoint (replaces RandomMatchGenerationSerializer)

---

## 6. VIEWS

### `MatchViewSet` (ModelViewSet)
- Use `StandardResponseMixin`
- Full CRUD
- Filters: division, tournament, match_type, status, player

### Custom Action: Register Results
- `POST /matches/{id}/scores/`
- Use `MatchScoreService`
- Body: `{"sets": [{"set_number": 1, "player1_score": 15, "player2_score": 12}, ...]}`
- Service calculates winner automatically based on `max_sets` and `points_per_set` of the match

### Endpoint: Generate Complete Bracket
- `POST /matches/generate-bracket/`
- Use `MatchBracketGenerationService`
- Body: 
  ```json
  {
    "division_id": 1,
    "max_sets": 5,        // Optional, default: 5
    "points_per_set": 15  // Optional, default: 15
  }
  ```
- Generates ALL bracket matches according to division format:
  - **Single Elimination (KNOCKOUT):** Creates matches M1, M2, M3... up to final
  - **Double Elimination (DOUBLE_SLASH):** Creates matches M1-Mn (winners) and LM1-LMn (losers)
- Returns list of created matches grouped by round

---

## 7. PERMISSIONS

- View matches: Public or authenticated
- Create/edit/delete: Tournament organization admins only
- Register results: Admins or involved players

---

## 8. URLS

- Register in `config/urls.py` under `/api/v1/matches/`
- Router for ViewSet
- URL for random generation

---

## 9. IMPORTANT VALIDATIONS

1. **Match Configuration (CONFIGURABLE):**
   - **Default:** 5 sets of 15 points each
   - Configurable when creating the match: `max_sets` (3-10) and `points_per_set` (1-50)
   - To win: need `(max_sets // 2) + 1` sets (e.g., 5 sets = 3 to win, 7 sets = 4 to win)
   - Validate scores are >= 0 and set winner >= `points_per_set`

2. **Match Code System:**
   - **Winners Bracket:** M1, M2, M3, M4, ... (Match 1, Match 2, etc.)
   - **Losers Bracket:** LM1, LM2, LM3, ... (Lost Match 1, Lost Match 2, etc.)
   - Codes must be unique per division (not globally)
   - Generate sequentially when creating the bracket

3. **Bracket Generation:**
   - **Single Elimination (KNOCKOUT):**
     - Create all necessary rounds up to final
     - Winners advance to next round
     - Connect matches with `next_match`
   - **Double Elimination (DOUBLE_SLASH):**
     - Create complete Winners Bracket
     - Create complete Losers Bracket (with codes LM1, LM2, etc.)
     - Create Grand Final between winners of both brackets
     - Handle Bracket Reset if necessary

4. **Singles vs Doubles:**
   - Singles: only player1 and player2
   - Doubles: player1 + partner1 vs player2 + partner2
   - For byes: player1 or player2 can be NULL

5. **Validate players in division:**
   - All players must have approved Involvement in the division
   - Use `Involvement.objects.filter(division=division, status=InvolvementStatus.APPROVED)`
   - In doubles: both players of the team must be approved

6. **Supported Formats:**
   - Only generate brackets for formats: `KNOCKOUT` (Single Elimination) and `DOUBLE_SLASH` (Double Elimination)
   - `ROUND_ROBIN` may require different logic (not included in this initial requirement)

---

## 10. TECHNICAL REQUIREMENTS

- ✅ Follow project's clean architecture
- ✅ All services with `@transaction.atomic` when necessary
- ✅ Exceptions with `error_code` for i18n
- ✅ Thin views, logic in services
- ✅ Type hints in all functions
- ✅ Docstrings in Spanish (NOTE: You should translate these docstrings to English as well if implementing)
- ✅ Unit and integration tests
- ✅ Query optimization (select_related, prefetch_related)
- ✅ Use `APIResponse` for all responses
- ✅ Logging of important operations

---

## 11. IMPLEMENTATION CHECKLIST

- [ ] Create `matches` app
- [ ] Create `Match` and `Set` models
- [ ] Create migrations
- [ ] Create exceptions with error_code
- [ ] Create services (MatchCreationService, MatchUpdateService, MatchDeletionService, MatchListService, MatchBracketGenerationService, MatchScoreService)
- [ ] Create serializers
- [ ] Create views and endpoints
- [ ] Create permissions
- [ ] Configure URLs
- [ ] Register in admin
- [ ] Create basic tests
- [ ] Verify with ruff check and ruff format

---

## IMPORTANT

- Review `apps/tournaments/models.py` to understand:
  - `TournamentDivision.format` (KNOCKOUT, DOUBLE_SLASH, ROUND_ROBIN)
  - `TournamentDivision.participant_type` (SINGLE, DOUBLES)
  - `Involvement` with approved players
- Review `apps/players/models.py` to understand `PlayerProfile`
- Follow patterns from `apps/tournaments/` as reference
- All error responses must include `error_code` in meta
- Matches can have `player1` or `player2` NULL to represent byes
- The `match_code` field is unique per division, not globally (use `unique_together` in Meta)

---

**Start by creating the models and then proceed with services and views!**
