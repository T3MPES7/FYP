import json
import csv
from datetime import datetime, timedelta

#Start time for timestamp
START_DATE = datetime(2024, 1, 1, 0, 0, 0)  

def convert_timestamp(sim_time):
    if isinstance(sim_time, (int, float)):  # if number
        converted_time = START_DATE + timedelta(minutes=sim_time)
        return converted_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  #YYYY-MM-DD HH:MM:SS.SSS
    return ""

def main():
    input_file = "MercuryLogs.json"       
    output_file = "CSVMercuryLogs.csv"

    # Columns for Process Mining
    columns = [
        #Main
        "case_id", "event_name", "timestamp", "event_type", "action",

        #Key Passenger
        "passenger_id", "itinerary", "status", "pax_type", "time_at_gate", "in_transit_to",

        #Delay and Cost 
        "delay_minutes", "delay", "cost_type", "cost_amount", "compensation", "soft_cost", "overnight",

        #Train & Flight 
        "connection_type", "train_uid", "stop_id", "train_operator_uid",

        #Reallocation Information
        "reallocation_options_itineraries", "reallocation_options_capacities",
        "reallocation_options_travelling_times", "reallocation_options_transfer_costs",
        "reallocation_options_arrival_times", "reallocation_options_departure_times",

        #Other 
        "aoc_uid", "pax_handler_uid"
        ]


    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", newline="", encoding="utf-8") as outfile:
        
        writer = csv.DictWriter(outfile, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for line in infile:
            if not line.strip():
                continue  #Skip if empty 
            
            data = json.loads(line)
            details = data.get("details", {})

            #Main attribute
            #passanger = passenger_id
            #Flight = flight_number
            FocusAttribute = details.get("passenger_id")
            if FocusAttribute is None:
                continue  #Skip events without a central attribute

            event_type = data.get("event_type", "")
            action = details.get("action", "")

            # skips useless events
            if event_type == "Initialization":
                continue

            row = {
                "case_id": FocusAttribute,  # The focus attribute
                "event_name": f"{event_type}-{action}" if action else event_type,
                "timestamp": convert_timestamp(data.get("timestamp", 0)), 
                "event_type": event_type,  
                "action": details.get("action", ""),
                
                # Key Passenger Details
                "passenger_id": details.get("passenger_id", ""),
                "itinerary": details.get("itinerary", ""),
                "status": details.get("status", ""),
                "pax_type": details.get("pax_type", ""),
                "time_at_gate": details.get("time_at_gate", ""),
                "in_transit_to": details.get("in_transit_to", ""),
                
                # Delay and Cost Information
                "delay_minutes": details.get("delay_minutes", ""),
                "delay": details.get("delay", ""),
                "cost_type": details.get("cost_type", ""),
                "cost_amount": details.get("cost_amount", ""),
                "compensation": details.get("compensation", ""),
                "soft_cost": details.get("soft_cost", ""),
                "overnight": details.get("overnight", ""),

                # Train & Flight Connection Details
                "connection_type": details.get("connection_type", ""),
                "train_uid": details.get("train_uid", ""),
                "stop_id": details.get("stop_id", ""),
                "train_operator_uid": details.get("train_operator_uid", ""),
                
                # Reallocation Information
                "reallocation_options_itineraries": details.get("reallocation_options", {}).get("itineraries", ""),
                "reallocation_options_capacities": details.get("reallocation_options", {}).get("capacities", ""),
                "reallocation_options_travelling_times": details.get("reallocation_options", {}).get("travelling_times", ""),
                "reallocation_options_transfer_costs": details.get("reallocation_options", {}).get("transfer_costs", ""),
                "reallocation_options_arrival_times": details.get("reallocation_options", {}).get("arrival_times", ""),
                "reallocation_options_departure_times": details.get("reallocation_options", {}).get("departure_times", ""),
                
                # Other Key Identifiers
                "aoc_uid": details.get("aoc_uid", ""),
                "pax_handler_uid": details.get("pax_handler_uid", ""),
            }

            # Creates row in CSV
            writer.writerow(row)


    print(f"Done! Created '{output_file}'")

if __name__ == "__main__":
    main()
