import csv
import os
import sys
import django
import datetime

# Setup Django
# Assuming default is config.settings.dev as per manage.py, but safe to use .base if .dev inherits or vice versa.
# Using what manage.py uses:
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.matches.models import Match

def parse_date(date_str):
    # Format: 2026-01-28 17:00:00+00
    # Python 3.7+ fromisoformat handles some, but +00 might need handling if not ideal.
    # The csv has "+00". strptime %z should handle it.
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z")
    except ValueError:
        # Fallback
        return datetime.datetime.strptime(date_str.split('+')[0], "%Y-%m-%d %H:%M:%S")

def main():
    input_file = 'updated_schedule.csv'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    updated_count = 0
    errors = []

    print("Starting database update...")
    
    with open(input_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            match_id = row['id']
            new_time_str = row['scheduled_at']
            new_location = row['location']
            
            try:
                match = Match.objects.get(id=match_id)
                
                # Parse time
                new_time = parse_date(new_time_str)
                
                # Update fields
                match.scheduled_at = new_time
                match.location = new_location
                
                # Save
                match.save()
                updated_count += 1
                
                # print(f"Updated Match {match_id}: {new_time} @ {new_location}")
                
            except Match.DoesNotExist:
                errors.append(f"Match ID {match_id} not found in DB.")
            except Exception as e:
                errors.append(f"Error updating Match ID {match_id}: {str(e)}")

    print("-" * 30)
    print(f"Update Complete.")
    print(f"Successfully updated: {updated_count}")
    
    if errors:
        print(f"Errors ({len(errors)}):")
        for err in errors:
            print(f" - {err}")
    else:
        print("No errors.")

if __name__ == "__main__":
    main()
