import datetime

# =================================================================================
# CLASS: AutoScaler
# PURPOSE: This class handles the logic for deciding when to add or remove servers.
#          It is the "brain" of the scaling operation.
# =================================================================================

class AutoScaler:
    """
    A class to manage autoscaling decisions based on load predictions.
    
    Attributes:
        max_capacity_per_server (int): The maximum number of requests a single server can handle per minute.
        cooldown_period_minutes (int): The waiting time (in minutes) after a scaling action before another can occur.
                                       This prevents 'flapping' (rapidly scaling up and down).
        cost_per_server_hour (float): The cost to run one server for one hour (in USD).
        last_scale_time (datetime): Stores the timestamp of the last scaling action.
    """

    def __init__(self, max_capacity_per_server=1000, cooldown_minutes=5, cost_per_server=0.45):
        """
        Constructor method to initialize the AutoScaler object.
        
        Args:
            max_capacity_per_server (int): Capacity of 1 server. Default is 1000 req/min.
            cooldown_minutes (int): Minutes to wait between scaling actions. Default is 5.
            cost_per_server (float): Cost in $ per hour. Default is $0.45.
        """
        self.max_capacity_per_server = max_capacity_per_server
        self.cooldown_period = datetime.timedelta(minutes=cooldown_minutes)
        self.cost_per_server_hour = cost_per_server
        
        # Initialize last_scale_time to a time far in the past so we can scale immediately if needed.
        # datetime.datetime.min is the earliest representable year.
        self.last_scale_time = datetime.datetime.min

    def decide_scaling_action(self, current_servers, predicted_load, current_time=None):
        """
        Decides whether to scale up, scale down, or maintain the current number of servers.

        Args:
            current_servers (int, >0): The number of servers currently running.
            predicted_load (float, >=0): The total number of requests predicted for the next time window.
            current_time (datetime, optional): The current timestamp. If None, uses datetime.datetime.now().

        Returns:
            dict: A dictionary containing the 'action', 'target_servers', and 'reason'.
        """
        
        # 1. Handle the 'current_time' argument.
        #    If the user didn't provide a time, we use the current system time.
        if current_time is None:
            current_time = datetime.datetime.now()

        # 2. Check for Cooldown to prevent Flapping.
        #    Flapping is when we scale up, then immediately scale down because the load dropped slightly.
        #    We check if enough time has passed since the last action.
        time_since_last_scale = current_time - self.last_scale_time
        
        # Note: We usually allow scaling UP during cooldown if it's an emergency (load >>> capacity),
        # but for this simple version, we will enforce cooldown strictly for stability.
        if time_since_last_scale < self.cooldown_period:
            return {
                "action": "maintain",
                "target_servers": current_servers,
                "reason": f"Cooldown active. Time since last scale: {time_since_last_scale}. Wait until {self.cooldown_period} passes."
            }

        # 3. Calculate Utilization.
        #    Utilization = (Predicted Load) / (Total Capacity of all servers)
        total_capacity = current_servers * self.max_capacity_per_server
        
        # Avoid division by zero if for some reason servers is 0 (should not happen in production but good practice)
        if total_capacity == 0:
            utilization = 1.0 # Infinite load effectively
        else:
            utilization = predicted_load / total_capacity

        # 4. Define Thresholds.
        #    SCALE UP logic: If utilization > 85%, we are in danger of crashing.
        #    SCALE DOWN logic: If utilization < 30%, we are wasting money.
        UP_THRESHOLD = 0.85
        DOWN_THRESHOLD = 0.30

        # 5. Make the Decision.
        action = "maintain"
        target_servers = current_servers
        reason = "Load is within the optimal range (30% - 85%)."

        if utilization > UP_THRESHOLD:
            # -- SCALE UP --
            # We add servers. How many?
            # Simple approach: Add 1 server.
            # Advanced approach: Calculate exactly how many are needed to bring utilization below target (e.g. 70%).
            # Let's use the simple approach for now, but loop to safe-guard.
            
            # While predicted load is still > 85% of new capacity, keep adding servers.
            # This ensures we add enough servers to handle a massive spike instantly.
            while (predicted_load / (target_servers * self.max_capacity_per_server)) > 0.70: # Aim for 70% utilization
                target_servers += 1
            
            action = "scale_up"
            reason = f"High Load! Predicted {predicted_load:.1f} reqs exceeds {UP_THRESHOLD*100}% of {current_servers} servers."
            
            # UPDATE STATE: Update the last_scale_time because we are taking action.
            self.last_scale_time = current_time

        elif utilization < DOWN_THRESHOLD and current_servers > 1:
            # -- SCALE DOWN --
            # Only scale down if we have more than 1 server (always keep 1 running).
            
            # Simple approach: Remove 1 server.
            target_servers -= 1
            
            # Double check: Will removing a server cause us to instantly jump above 85% again?
            # If so, don't do it! prediction is tricky.
            new_capacity = target_servers * self.max_capacity_per_server
            new_utilization = predicted_load / new_capacity
            
            if new_utilization > 0.80:
                # Abort scaling down, it's too risky.
                target_servers += 1 # Reset
                action = "maintain"
                reason = "Scaling down would cause utilization to spike above 80%. Holding current capacity."
            else:
                action = "scale_down"
                reason = f"Low Load. Predicted {predicted_load:.1f} reqs is below {DOWN_THRESHOLD*100}% of capacity."
                
                # UPDATE STATE: Update last_scale_time
                self.last_scale_time = current_time

        # 6. Return the detailed result
        return {
            "action": action,
            "target_servers": target_servers,
            "predicted_load": predicted_load,
            "reason": reason,
            "timestamp": current_time.isoformat()
        }

    def calculate_cost(self, server_count, duration_hours=1):
        """
        Simple helper to calculate cost.
        Total Cost = Number of Servers * Cost per Server per Hour * Duration
        """
        return server_count * self.cost_per_server_hour * duration_hours
