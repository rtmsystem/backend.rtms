from apps.tournaments.models import TournamentDivision, TournamentGroup
from apps.matches.models import Match

try:
    division = TournamentDivision.objects.get(pk=21)
    print(f"Division: {division.name} (ID: {division.id})")
    
    groups = TournamentGroup.objects.filter(division=division)
    print(f"Groups count: {groups.count()}")
    for group in groups:
        print(f"Group ID: {group.id}, Name: {group.name}, Group Number: {group.group_number}")
        
    matches = Match.objects.filter(division=division)
    print(f"Matches count: {matches.count()}")
    for match in matches:
        print(f"Match ID: {match.id}, Code: {match.match_code}, Round: {match.round_number}, Status: {match.status}")

    # Try the specific query
    for group in groups:
        matches_query = Match.objects.filter(
            division=division,
            round_number=-group.group_number,
            status='completed' # MatchStatus.COMPLETED is 'completed'
        )
        print(f"Query for Group {group.group_number} (round {-group.group_number}): Found {matches_query.count()} matches")

except Exception as e:
    print(f"Error: {e}")
