import csv
import datetime
from collections import defaultdict

def parse_date(date_str):
    # Format: 2026-01-28 23:00:00+00
    # handling the timezone usually requires strptime with %z, or just split
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S+00")
    except ValueError:
        # Fallback or simple split if needed, but the sample data seems consistent
        return datetime.datetime.strptime(date_str.split('+')[0], "%Y-%m-%d %H:%M:%S")

def main():
    input_file = 'data-1769482132929.csv'
    output_file = 'updated_schedule.csv'

    matches = []
    locations = set()
    
    # 1. Load Data
    with open(input_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
            if row['location']:
                locations.add(row['location'])
    
    sorted_locations = sorted(list(locations))
    
    # 2. Define Constraints
    start_date = datetime.date(2026, 1, 28)
    end_date = datetime.date(2026, 1, 31)
    
    # Time range: 17:00 to 22:40 (10:40 PM)
    # 22:40 is the end of the last match, so the last match starts at 22:00
    day_start_hour = 17
    day_start_min = 0
    # The end limit for *starting* a match:
    # If games end at 10:40 PM, and last 40 mins, the last start time is 10:00 PM (22:00).
    # So we can generate slots until slot_end <= 22:40.
    
    match_duration_minutes = 40
    
    # Generate all possible time slots
    all_slots = []
    
    current_date = start_date
    while current_date <= end_date:
        start_time = datetime.datetime.combine(current_date, datetime.time(day_start_hour, day_start_min))
        # End limit is 22:40
        end_time_limit = datetime.datetime.combine(current_date, datetime.time(22, 40))
        
        current_slot_start = start_time
        while current_slot_start + datetime.timedelta(minutes=match_duration_minutes) <= end_time_limit:
            slot_end = current_slot_start + datetime.timedelta(minutes=match_duration_minutes)
            all_slots.append((current_slot_start, slot_end))
            current_slot_start = slot_end
            
        current_date += datetime.timedelta(days=1)
        
    print(f"Total slots per court: {len(all_slots)}")
    print(f"Total courts: {len(sorted_locations)}")
    print(f"Total capacity: {len(all_slots) * len(sorted_locations)}")
    
    # Analyze player match counts
    player_match_counts = defaultdict(int)
    for match in matches:
        player_match_counts[match['player1_id']] += 1
        player_match_counts[match['player2_id']] += 1
    
    # Sort matches by "most constrained match first"
    matches.sort(key=lambda m: player_match_counts[m['player1_id']] + player_match_counts[m['player2_id']], reverse=True)

    print("--- Player Match Counts ---")
    most_games = 0
    for p, count in player_match_counts.items():
        if count > most_games:
            most_games = count
    print(f"Max games for any single player: {most_games}")
    print("---------------------------")


    # 3. Schedule Matches
    # Tracking:
    player_daily_count = defaultdict(lambda: defaultdict(int)) # Date -> Player -> Count
    court_schedule = defaultdict(set)        # Date+Time -> Set of locations occupied
    player_busy_at = defaultdict(set)        # Date+Time -> Set of players busy
    
    updated_matches = []
    unscheduled_matches = []
    
    # New Constraint: Allow 2 games per day
    MAX_GAMES_PER_DAY = 2

    for match in matches:
        p1 = match['player1_id']
        p2 = match['player2_id']
        match_id = match['id']
        
        assigned = False
        
        # Try to find a slot
        for slot_start, slot_end in all_slots:
            slot_date_str = slot_start.date().isoformat()
            
            # Constraint: Max games per day
            if player_daily_count[slot_date_str][p1] >= MAX_GAMES_PER_DAY:
                continue
            if player_daily_count[slot_date_str][p2] >= MAX_GAMES_PER_DAY:
                continue
                
            # Constraint: Player cannot be in two places at once
            if p1 in player_busy_at[slot_start] or p2 in player_busy_at[slot_start]:
                continue
            
            # Constraint: Find a free court
            free_location = None
            for loc in sorted_locations:
                if loc not in court_schedule[slot_start]:
                    free_location = loc
                    break
            
            if free_location:
                # Assign this slot
                match['scheduled_at'] = slot_start.strftime("%Y-%m-%d %H:%M:%S") + "+00"
                match['location'] = free_location
                
                # Update tracking
                player_daily_count[slot_date_str][p1] += 1
                player_daily_count[slot_date_str][p2] += 1
                court_schedule[slot_start].add(free_location)
                player_busy_at[slot_start].add(p1)
                player_busy_at[slot_start].add(p2)
                
                updated_matches.append(match)
                assigned = True
                break
        
        if not assigned:
            print(f"Warning: Could not schedule match ID {match_id} (Players {p1} vs {p2})")
            unscheduled_matches.append(match)

    # 4. Save Updated CSV
    fieldnames = ['id', 'scheduled_at', 'location', 'division_id', 'player1_id', 'player2_id']
    
    with open(output_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_matches)
        
    print(f"Successfully scheduled {len(updated_matches)} matches.")
    if unscheduled_matches:
        print(f"Failed to schedule {len(unscheduled_matches)} matches due to constraints.")

if __name__ == "__main__":
    main()
