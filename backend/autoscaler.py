import datetime

# =================================================================================
# CLASS: AutoScaler
# ROLE: M3 (Logic / Backend)
# PURPOSE: The "Brain" of the system. Decides when to Scale Up or Scale Down.
# =================================================================================

class AutoScaler:
    """
    AutoScaler manages the number of active servers based on predicted traffic.
    
    CORE CONCEPTS:
    --------------
    1. CAPACITY: How many requests can one server handle? (e.g., 1000 req/min)
    2. UTILIZATION: How busy are we? (Load / Total Capacity)
       - If > 85%: System is stressed. Scale UP.
       - If < 30%: System is idle. Scale DOWN.
    3. COOLDOWN: Wait time between actions.
       - Prevents "Flapping" (rapid up/down toggling) which hurts stability.
    """

    def __init__(self, max_capacity_per_server=1000, cooldown_minutes=5, cost_per_server=0.45):
        """
        Initialize the AutoScaler.
        
        ARGS:
        -----
        max_capacity_per_server (int): Requests/min one server can handle.
        cooldown_minutes (int): Time to wait after scaling before scaling again.
        cost_per_server (float): Hourly cost in USD (e.g., $0.45/hour on AWS).
        """
        self.max_capacity_per_server = max_capacity_per_server
        self.cooldown_period = datetime.timedelta(minutes=cooldown_minutes)
        self.cost_per_server_hour = cost_per_server
        
        # State: When did we last scale? Initialize to a valid old date so we can start immediately.
        self.last_scale_time = datetime.datetime(1970, 1, 1)

    def decide_scaling_action(self, current_servers, predicted_load, current_time=None):
        """
        THE MAIN LOGIC FUNCTION.
        
        INPUTS:
        -------
        - current_servers: How many servers we have running NOW.
        - predicted_load: How many requests the AI thinks we will have SOON.
        
        RETURNS:
        --------
        - action: "scale_up", "scale_down", or "maintain"
        - target_servers: The new desired count.
        """
        
        # 1. Get Current Time
        if current_time is None:
            current_time = datetime.datetime.now()

        # 2. Check Cooldown (Safety mechanism)
        time_since_last_scale = current_time - self.last_scale_time
        
        # If we scaled recently (within cooldown period), DON'T DO ANYTHING.
        # Exception: We stick to strict cooldown for this demo to show "stability".
        if time_since_last_scale < self.cooldown_period:
            return {
                "action": "maintain",
                "target_servers": current_servers,
                "reason": f"❄️ Cooldown active. Wait {self.cooldown_period}."
            }

        # 3. Calculate Utilization (How full is the "Bucket"?)
        total_capacity = current_servers * self.max_capacity_per_server
        
        if total_capacity == 0:
            utilization = 1.0 # Avoid division by zero
        else:
            utilization = predicted_load / total_capacity

        # 4. Define Thresholds (Rules of Engagement)
        # > 85% full? DANGER! Add servers.
        # < 30% full? WASTE! Remove servers.
        UP_THRESHOLD = 0.85
        DOWN_THRESHOLD = 0.30

        # 5. Make the Decision
        action = "maintain"
        target_servers = current_servers
        reason = "Load is stable (30% - 85%)."

        if utilization > UP_THRESHOLD:
            # === SCALE UP CASE ===
            # Utilization is too high! Risk of crash.
            
            # Simple Algorithm: Add servers one by one until we are safe (below 70%).
            while (predicted_load / (target_servers * self.max_capacity_per_server)) > 0.70:
                target_servers += 1
            
            action = "scale_up"
            reason = f"🔥 High Load! Predicted {predicted_load:.0f} reqs > {UP_THRESHOLD:.0%} capacity."
            
            # Reset the cooldown timer
            self.last_scale_time = current_time

        elif utilization < DOWN_THRESHOLD and current_servers > 1:
            # === SCALE DOWN CASE ===
            # Utilization is too low. We are burning money.
            
            # Try removing 1 server.
            potential_servers = target_servers - 1
            
            # SAFETY CHECK: Will removing a server cause an immediate crash?
            new_capacity = potential_servers * self.max_capacity_per_server
            new_utilization = predicted_load / new_capacity
            
            if new_utilization > 0.80:
                # Too risky! Don't scale down.
                action = "maintain"
                reason = "⚠️ Scaling down is unsafe (would hit >80% utilization)."
            else:
                target_servers -= 1
                action = "scale_down"
                reason = f"💸 Low Load. Saving costs."
                
                # Reset the cooldown timer
                self.last_scale_time = current_time

        # 6. Return Decision
        return {
            "action": action,
            "target_servers": target_servers,
            "predicted_load": predicted_load,
            "reason": reason,
            "timestamp": current_time.isoformat()
        }

    def calculate_cost(self, server_count, duration_hours=1):
        """Helper to calculate $$ cost."""
        return server_count * self.cost_per_server_hour * duration_hours
