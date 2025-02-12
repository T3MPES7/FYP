import json
from collections import defaultdict

# Recursively count occurrences of attributes from the MercuryLogs.json.
def CountAttributes(data, prefix, AttributeCounts):
    if isinstance(data, dict):  
        for key, value in data.items():
            AttributeName = f"{prefix}.{key}" if prefix else key
            AttributeCounts[AttributeName] += 1  # Count occurrences
            
            # Recursively process nested dictionaries/lists
            CountAttributes(value, AttributeName, AttributeCounts)

    elif isinstance(data, list):  # If the data is a list
        for item in data:
            CountAttributes(item, prefix, AttributeCounts)  # Process each list item

def main():
    File = "MercuryLogs.json"

    # Holds counts of all attributes
    AttributeCounts = defaultdict(int)
    
    # Holds event type occurrence counts for those that have passanger ID
    EventTypeCounts = defaultdict(int)

    # Open the file
    with open(File, "r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue  # Skip if line is blank
                
            data = json.loads(line)
            details = data.get("details", {})
            event_type = data.get("event_type", "UnknownEvent")#Get event type
            
            # Primary attribute to check for: passenger_id
            if "passenger_id" in details:
                CountAttributes(data, "root", AttributeCounts)  # Count all attributes
                EventTypeCounts[event_type] += 1  # Count occurrences of event type

    #Sort attribute by frequency
    SortedAttributes = sorted(AttributeCounts.items(), key=lambda x: x[1], reverse=True)

    # Display total attribute occurrences
    print("=== Attributes Count ===")
    for attr, count in SortedAttributes:
        print(f"{attr}: {count}")

    #Sort event type by frequency
    SortedEventTypes = sorted(EventTypeCounts.items(), key=lambda x: x[1], reverse=True)

    print("\n=== Event Type Occurrences ===")
    for event_type, count in SortedEventTypes:
        print(f"{event_type}: {count}")

if __name__ == "__main__":
    main()
